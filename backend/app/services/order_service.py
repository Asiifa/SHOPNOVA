"""Order placement with PostgreSQL-enforced inventory validation.

Checkout creates the order in a PLACED (pending-inventory) state inside a single
PostgreSQL transaction together with an `order.created` outbox record. Stock is
NOT decremented here. The Kafka inventory consumer locks inventory rows,
validates stock, and confirms or rejects the order asynchronously.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.cart import Cart, CartItem
from app.models.catalog import Product
from app.models.inventory import InventoryTransaction
from app.models.order import Order, OrderItem, OrderStatus, PaymentMethod, PaymentStatus
from app.models.user import CustomerAddress
from app.services.outbox import enqueue_event

logger = logging.getLogger(__name__)
FREE_SHIPPING_THRESHOLD = Decimal("999.00")
FLAT_SHIPPING = Decimal("49.00")


def _unit_price(product: Product) -> Decimal:
    if product.discount_price is not None:
        return Decimal(product.discount_price)
    return Decimal(product.price)


def _order_number() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"SN-{stamp}-{uuid4().hex[:8].upper()}"


def place_order(
    session: Session,
    *,
    customer_id: UUID,
    address_id: UUID,
    payment_method: PaymentMethod,
) -> Order:
    address = session.scalar(
        select(CustomerAddress).where(
            CustomerAddress.id == address_id, CustomerAddress.customer_id == customer_id
        )
    )
    if not address:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Delivery address not found.")

    cart = session.scalar(
        select(Cart)
        .where(Cart.customer_id == customer_id)
        .options(
            joinedload(Cart.items)
            .joinedload(CartItem.product)
            .joinedload(Product.inventory)
        )
    )
    if not cart or not cart.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cart is empty.")

    correlation_id = uuid4()
    subtotal = Decimal("0.00")
    line_plan: list[tuple[CartItem, Product, Decimal, int]] = []

    # Validate every line against the live PostgreSQL catalogue and inventory.
    # Prices are snapshotted into order_items so they remain historical even if
    # the catalogue price changes later.
    for item in cart.items:
        product = item.product
        if not product or not product.is_active:
            session.rollback()
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"A product in the cart is no longer available.",
            )
        qty = item.quantity
        if qty < 1:
            session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid quantity.")
        available = product.inventory.available_quantity if product.inventory else 0
        if available < qty:
            session.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Insufficient stock for {product.name}.",
            )
        price = _unit_price(product)
        line_plan.append((item, product, price, qty))
        subtotal += price * qty

    shipping = Decimal("0.00") if subtotal >= FREE_SHIPPING_THRESHOLD else FLAT_SHIPPING
    total = subtotal + shipping
    pay_status = PaymentStatus.COD_PENDING if payment_method == PaymentMethod.COD else PaymentStatus.PAID

    order = Order(
        order_number=_order_number(),
        customer_id=customer_id,
        address_id=address_id,
        total_amount=total,
        shipping_amount=shipping,
        payment_method=payment_method,
        payment_status=pay_status,
        order_status=OrderStatus.PLACED,
    )
    session.add(order)
    session.flush()

    items_payload = []
    for item, product, price, qty in line_plan:
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                unit_price=price,
                quantity=qty,
                line_total=price * qty,
            )
        )
        product.sold_count = (product.sold_count or 0) + qty
        items_payload.append(
            {
                "product_id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "quantity": qty,
                "unit_price": str(price),
            }
        )

    enqueue_event(
        session,
        event_type="order.created",
        aggregate_id=str(order.id),
        topic_key="order",
        correlation_id=correlation_id,
        payload={
            "order_id": str(order.id),
            "order_number": order.order_number,
            "customer_id": str(customer_id),
            "total_amount": str(total),
            "payment_method": payment_method.value,
            "items": items_payload,
        },
    )

    # The cart is cleared only once the inventory consumer settles the order
    # (CONFIRMED or CANCELLED). Until then the cart is preserved so a rejected
    # order does not lose the customer's selection.
    session.commit()
    session.refresh(order)
    logger.info("Order %s placed in PLACED state; order.created published to outbox", order.order_number)
    return order


def clear_cart_for_customer(session: Session, customer_id: UUID) -> None:
    cart = session.scalar(select(Cart).where(Cart.customer_id == customer_id))
    if cart:
        for item in list(cart.items):
            session.delete(item)


def concurrent_reserve_sql() -> str:
    """Documented SQL used by tests to prove atomic reservation."""
    return """
    UPDATE inventory
    SET available_quantity = available_quantity - :qty,
        reserved_quantity = reserved_quantity + :qty
    WHERE product_id = :product_id
      AND available_quantity >= :qty
    """
