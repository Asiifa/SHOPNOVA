from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_admin
from app.core.config import get_settings
from app.models.catalog import Product
from app.models.events import OutboxEvent, ProcessedEvent
from app.models.inventory import Inventory, InventoryTransaction
from app.models.notification import Notification
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.schemas.admin import StatusBody
from app.services.outbox import enqueue_event

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    order_count = db.scalar(select(func.count()).select_from(Order)) or 0
    revenue = db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0))) or 0
    customer_count = db.scalar(select(func.count()).select_from(User).where(User.role == UserRole.CUSTOMER)) or 0
    product_count = db.scalar(select(func.count()).select_from(Product).where(Product.is_active.is_(True))) or 0
    unpublished = db.scalar(select(func.count()).select_from(OutboxEvent).where(OutboxEvent.published.is_(False))) or 0
    processed = db.scalar(select(func.count()).select_from(ProcessedEvent)) or 0
    low_stock = db.scalar(select(func.count()).select_from(Inventory).where(Inventory.available_quantity < 5)) or 0
    return {
        "orders": order_count,
        "revenue_inr": float(revenue),
        "customers": customer_count,
        "active_products": product_count,
        "unpublished_outbox": unpublished,
        "processed_events": processed,
        "low_stock_skus": low_stock,
    }


@router.get("/orders")
def admin_orders(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    total = db.scalar(select(func.count()).select_from(Order)) or 0
    rows = db.scalars(
        select(Order)
        .options(joinedload(Order.items), joinedload(Order.customer))
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": str(o.id),
                "order_number": o.order_number,
                "customer_email": o.customer.email if o.customer else None,
                "total_amount": float(o.total_amount),
                "order_status": o.order_status.value,
                "payment_status": o.payment_status.value,
                "created_at": o.created_at.isoformat(),
            }
            for o in rows
        ],
    }


@router.patch("/orders/{order_id}/status")
def update_status(
    order_id: UUID, body: StatusBody, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> dict:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    order.order_status = body.order_status
    enqueue_event(
        db,
        event_type="order.status.updated",
        aggregate_id=str(order.id),
        topic_key="order",
        payload={
            "order_id": str(order.id),
            "order_number": order.order_number,
            "order_status": body.order_status.value,
        },
    )
    db.commit()
    return {"id": str(order.id), "order_status": order.order_status.value}


@router.get("/events")
def events(db: Session = Depends(get_db), admin: User = Depends(require_admin), limit: int = Query(50, le=200)) -> dict:
    outbox = db.scalars(select(OutboxEvent).order_by(OutboxEvent.created_at.desc()).limit(limit)).all()
    processed = db.scalars(select(ProcessedEvent).order_by(ProcessedEvent.processed_at.desc()).limit(limit)).all()
    return {
        "outbox": [
            {
                "event_id": str(e.event_id),
                "event_type": e.event_type,
                "topic": e.topic,
                "published": e.published,
                "publish_attempts": e.publish_attempts,
                "created_at": e.created_at.isoformat(),
                "last_error": e.last_error,
            }
            for e in outbox
        ],
        "processed": [
            {
                "event_id": str(e.event_id),
                "consumer_name": e.consumer_name,
                "event_type": e.event_type,
                "processed_at": e.processed_at.isoformat(),
            }
            for e in processed
        ],
    }


@router.get("/inventory/history")
def inventory_history(
    db: Session = Depends(get_db), admin: User = Depends(require_admin), limit: int = Query(50, le=200)
) -> list[dict]:
    rows = db.scalars(select(InventoryTransaction).order_by(InventoryTransaction.created_at.desc()).limit(limit)).all()
    return [
        {
            "id": str(r.id),
            "product_id": str(r.product_id),
            "order_id": str(r.order_id) if r.order_id else None,
            "change_type": r.change_type,
            "quantity_delta": r.quantity_delta,
            "reason": r.reason,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/customers")
def customers(db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> list[dict]:
    rows = db.scalars(select(User).where(User.role == UserRole.CUSTOMER).order_by(User.created_at.desc())).all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in rows
    ]


@router.get("/notifications")
def notifications(db: Session = Depends(get_db), admin: User = Depends(require_admin), limit: int = 50) -> list[dict]:
    rows = db.scalars(select(Notification).order_by(Notification.created_at.desc()).limit(limit)).all()
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "body": n.body,
            "created_at": n.created_at.isoformat(),
            "customer_id": str(n.customer_id) if n.customer_id else None,
        }
        for n in rows
    ]


@router.get("/system-health")
def system_health(admin: User = Depends(require_admin)) -> dict:
    settings = get_settings()
    return {
        "postgres": {
            "service": settings.aiven_pg_service,
            "configured": settings.postgres_configured(),
            "sslmode": settings.postgres_sslmode,
        },
        "kafka": {
            "service": settings.aiven_kafka_service,
            "configured": settings.kafka_configured(),
            "protocol": settings.kafka_security_protocol,
            "note": "Inkless: Kafka transactions and compacted topics are not used.",
        },
        "opensearch": {
            "service": settings.aiven_os_service,
            "configured": settings.opensearch_configured(),
            "verify_certs": settings.opensearch_verify_certs,
            "index": settings.opensearch_index,
        },
    }
