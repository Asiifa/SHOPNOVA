from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.order import Order, OrderItem, PaymentMethod
from app.models.user import User
from app.schemas.orders import OrderOut, PlaceOrderBody
from app.schemas.common import Page
from app.services.order_service import place_order

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _to_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        order_number=order.order_number,
        total_amount=float(order.total_amount),
        shipping_amount=float(order.shipping_amount),
        payment_method=order.payment_method.value,
        payment_status=order.payment_status.value,
        order_status=order.order_status.value,
        created_at=order.created_at,
        items=[
            OrderItemOut(
                product_id=i.product_id,
                product_name=i.product_name,
                sku=i.sku,
                unit_price=float(i.unit_price),
                quantity=i.quantity,
                line_total=float(i.line_total),
            )
            for i in order.items
        ],
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    body: PlaceOrderBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> OrderOut:
    order = place_order(db, customer_id=user.id, address_id=body.address_id, payment_method=body.payment_method)
    order = db.scalar(select(Order).options(joinedload(Order.items)).where(Order.id == order.id))
    return _to_out(order)


@router.get("", response_model=Page[OrderOut])
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
) -> Page[OrderOut]:
    filters = [Order.customer_id == user.id]
    total = db.scalar(select(func.count()).select_from(Order).where(*filters)) or 0
    rows = db.scalars(
        select(Order)
        .options(joinedload(Order.items))
        .where(*filters)
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return Page(items=[_to_out(o) for o in rows], total=total, page=page, page_size=page_size)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> OrderOut:
    order = db.scalar(select(Order).options(joinedload(Order.items)).where(Order.id == order_id))
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    if order.customer_id != user.id and user.role.value != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to view this order")
    return _to_out(order)
