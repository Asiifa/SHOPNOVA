"""Unit tests for the order/inventory flow that run without Aiven credentials.

An in-memory SQLite database stands in for PostgreSQL so business rules can be
validated locally: pending-inventory order placement, stock reservation,
confirmation, rejection, idempotency and the outbox.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.cart import Cart, CartItem
from app.models.catalog import Category, Product
from app.models.inventory import Inventory
from app.models.order import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.models.user import CustomerAddress, User, UserRole
from app.services.order_service import place_order

pytestmark = pytest.mark.unit


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


def _seed(session: Session):
    category = Category(name="Electronics", slug="electronics")
    session.add(category)
    session.flush()
    product = Product(
        name="Bluetooth Earphones",
        slug="bluetooth-earphones",
        description="Wireless earphones",
        sku="SN-TEST-001",
        category_id=category.id,
        brand="TestBrand",
        price=Decimal("1999.00"),
        city="Bengaluru",
        image_url="https://example.com/img.jpg",
        is_active=True,
    )
    session.add(product)
    session.flush()
    session.add(Inventory(product_id=product.id, available_quantity=2, reserved_quantity=0))
    user = User(
        email="buyer@example.com",
        full_name="Buyer",
        password_hash="x",
        role=UserRole.CUSTOMER,
    )
    session.add(user)
    session.flush()
    session.add(Cart(customer_id=user.id))
    session.flush()
    session.add(
        CustomerAddress(
            customer_id=user.id,
            label="Home",
            full_name="Buyer",
            phone="9876500001",
            line1="1, Test Street",
            city="Bengaluru",
            state="Karnataka",
            pin_code="560095",
            is_default=True,
        )
    )
    session.commit()
    cart = session.query(Cart).filter_by(customer_id=user.id).one()
    address = (
        session.query(CustomerAddress).filter_by(customer_id=user.id).one()
    )
    session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=1))
    session.commit()
    return user.id, product.id, address.id


def test_place_order_is_pending_inventory(session: Session):
    user_id, product_id, _address_id = _seed(session)
    order = place_order(
        session,
        customer_id=user_id,
        address_id=_address_id,
        payment_method=PaymentMethod.COD,
    )
    assert order.order_status == OrderStatus.PLACED
    assert len(order.items) == 1
    assert order.items[0].unit_price == Decimal("1999.00")
    assert order.items[0].line_total == Decimal("1999.00")
    # Stock must NOT be decremented by order placement.
    inventory = session.get(Inventory, product_id)
    assert inventory.available_quantity == 2
    # The order.created outbox record must exist and be unpublished.
    from app.models.events import OutboxEvent

    rows = session.query(OutboxEvent).filter_by(event_type="order.created").all()
    assert len(rows) == 1
    assert rows[0].published is False


def test_insufficient_stock_rejected(session: Session):
    user_id, product_id, _address_id = _seed(session)
    from app.models.order import OrderStatus
    # Exhaust stock directly in inventory.
    session.query(Inventory).filter_by(product_id=product_id).update(
        {"available_quantity": 0}
    )
    session.commit()
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        place_order(
            session,
            customer_id=user_id,
            address_id=_address_id,
            payment_method=PaymentMethod.COD,
        )
    assert exc.value.status_code == 409
    assert session.query(Order).count() == 0


def test_consumer_confirms_and_reserves_stock(session: Session):
    user_id, product_id, _address_id = _seed(session)
    order = place_order(
        session,
        customer_id=user_id,
        address_id=_address_id,
        payment_method=PaymentMethod.COD,
    )
    assert order.order_status == OrderStatus.PLACED

    # Simulate the inventory consumer processing order.created once.
    from consumers.inventory_consumer import handle

    event = {
        "event_type": "order.created",
        "event_id": str(uuid4()),
        "payload": {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "customer_id": str(user_id),
        },
    }
    handle(session, event)
    session.commit()

    order = session.get(Order, order.id)
    assert order.order_status == OrderStatus.CONFIRMED
    inventory = session.get(Inventory, product_id)
    assert inventory.available_quantity == 1
    assert inventory.reserved_quantity == 1
    from app.models.events import OutboxEvent, ProcessedEvent

    outbox_types = {
        r.event_type for r in session.query(OutboxEvent).filter_by(aggregate_id=str(order.id)).all()
    }
    assert "order.confirmed" in outbox_types
    assert "inventory.changed" in outbox_types
    assert session.query(ProcessedEvent).count() == 1


def test_consumer_rejects_when_insufficient_stock(session: Session):
    user_id, product_id, _address_id = _seed(session)
    # Order is placed while stock exists (2 units), so placement succeeds.
    order = place_order(
        session,
        customer_id=user_id,
        address_id=_address_id,
        payment_method=PaymentMethod.COD,
    )
    assert order.order_status == OrderStatus.PLACED
    # Stock is exhausted before the consumer runs.
    session.query(Inventory).filter_by(product_id=product_id).update(
        {"available_quantity": 0}
    )
    session.commit()

    from consumers.inventory_consumer import handle

    event = {
        "event_type": "order.created",
        "event_id": str(uuid4()),
        "payload": {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "customer_id": str(user_id),
        },
    }
    handle(session, event)
    session.commit()

    order = session.get(Order, order.id)
    assert order.order_status == OrderStatus.CANCELLED
    inventory = session.get(Inventory, product_id)
    assert inventory.available_quantity == 0
    from app.models.events import OutboxEvent

    outbox_types = {
        r.event_type
        for r in session.query(OutboxEvent).filter_by(aggregate_id=str(order.id)).all()
    }
    assert "order.rejected" in outbox_types
    assert "inventory.changed" not in outbox_types


def test_consumer_idempotent_no_double_decrement(session: Session):
    user_id, product_id, _address_id = _seed(session)
    order = place_order(
        session,
        customer_id=user_id,
        address_id=_address_id,
        payment_method=PaymentMethod.COD,
    )

    from consumers.inventory_consumer import handle

    event = {
        "event_type": "order.created",
        "event_id": str(uuid4()),
        "payload": {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "customer_id": str(user_id),
        },
    }
    handle(session, event)
    session.commit()
    handle(session, event)  # duplicate delivery
    session.commit()

    order = session.get(Order, order.id)
    assert order.order_status == OrderStatus.CONFIRMED
    inventory = session.get(Inventory, product_id)
    assert inventory.available_quantity == 1  # decremented exactly once
    from app.models.events import ProcessedEvent

    assert session.query(ProcessedEvent).count() == 1
