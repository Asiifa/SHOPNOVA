"""Inventory consumer: authoritative stock reservation for PLACED orders.

Consumes `order.created` events from Kafka (Aiven Inkless; no Kafka transactions).
For each event, idempotently:

1. Checks `processed_events` so duplicate deliveries are skipped.
2. Locks the order's inventory rows in deterministic product_id order
   (`SELECT ... FOR UPDATE ORDER BY product_id`) to prevent deadlocks and
   overselling between concurrent consumers.
3. Validates every item's quantity against locked `available_quantity`.
4. Decrements stock only when the complete order can be fulfilled, records
   `inventory_transactions`, flips the order to CONFIRMED or CANCELLED.
5. Writes `inventory.changed` and `order.confirmed` / `order.rejected` outbox
   records in the SAME PostgreSQL transaction.
6. Records the processed event and commits. Kafka offsets are committed only
   after this transaction succeeds.

Kafka is never the source of truth for stock; PostgreSQL is.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.inventory import Inventory, InventoryTransaction
from app.models.order import Order, OrderStatus
from app.services.order_service import clear_cart_for_customer
from app.services.outbox import enqueue_event
from consumers.runtime import already_processed, mark_processed, run_consumer

CONSUMER = "inventory-processor"
logger = logging.getLogger(__name__)


def _reject(session: Session, order: Order, reason: str) -> None:
    order.order_status = OrderStatus.CANCELLED
    enqueue_event(
        session,
        event_type="order.rejected",
        aggregate_id=str(order.id),
        topic_key="order",
        payload={
            "order_id": str(order.id),
            "order_number": order.order_number,
            "order_status": OrderStatus.CANCELLED.value,
            "reason": reason,
        },
    )
    clear_cart_for_customer(session, order.customer_id)
    logger.warning("Order %s rejected: %s", order.order_number, reason)


def _process(session: Session, order: Order) -> None:
    # Lock inventory rows in deterministic order so two consumers handling
    # different orders for the same products cannot deadlock. Every consumer
    # acquires locks in the same product_id sequence.
    product_ids = sorted({item.product_id for item in order.items})
    rows = (
        session.execute(
            select(Inventory)
            .where(Inventory.product_id.in_(product_ids))
            .order_by(Inventory.product_id)
            .with_for_update()
        )
        .scalars()
        .all()
    )
    inventory_by_id = {row.product_id: row for row in rows}

    # Validate the complete order against the locked rows before changing anything.
    for item in order.items:
        inventory = inventory_by_id.get(item.product_id)
        available = inventory.available_quantity if inventory else 0
        if available < item.quantity:
            _reject(session, order, f"Insufficient stock for product {item.product_id}")
            return

    # All items satisfiable: decrement stock, record movements, confirm.
    for item in order.items:
        inventory = inventory_by_id[item.product_id]
        inventory.available_quantity -= item.quantity
        inventory.reserved_quantity += item.quantity
        session.add(
            InventoryTransaction(
                product_id=item.product_id,
                order_id=order.id,
                change_type="RESERVE",
                quantity_delta=-item.quantity,
                reason=f"Order {order.order_number}",
            )
        )

    order.order_status = OrderStatus.CONFIRMED
    enqueue_event(
        session,
        event_type="order.confirmed",
        aggregate_id=str(order.id),
        topic_key="order",
        payload={
            "order_id": str(order.id),
            "order_number": order.order_number,
            "order_status": OrderStatus.CONFIRMED.value,
        },
    )
    enqueue_event(
        session,
        event_type="inventory.changed",
        aggregate_id=str(order.id),
        topic_key="inventory",
        payload={
            "order_id": str(order.id),
            "order_number": order.order_number,
            "items": [
                {
                    "product_id": str(item.product_id),
                    "quantity_delta": -item.quantity,
                    "reason": "order_reserve",
                }
                for item in order.items
            ],
        },
    )
    clear_cart_for_customer(session, order.customer_id)
    logger.info("Order %s confirmed; stock reserved in PostgreSQL", order.order_number)


def handle(session: Session, value: dict) -> None:
    if value.get("event_type") != "order.created":
        return
    event_id = UUID(value["event_id"])
    if already_processed(session, CONSUMER, event_id):
        return

    payload = value.get("payload") or {}
    order_id = UUID(payload["order_id"])
    order = session.scalar(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    if not order:
        mark_processed(session, CONSUMER, event_id, value["event_type"])
        session.commit()
        return

    if order.order_status != OrderStatus.PLACED:
        # Already settled by an earlier delivery of the same logical event.
        mark_processed(session, CONSUMER, event_id, value["event_type"])
        session.commit()
        return

    try:
        _process(session, order)
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Inventory consumer failed for order %s", order_id)
        raise
    mark_processed(session, CONSUMER, event_id, value["event_type"])
    session.commit()


async def main() -> None:
    topics = get_settings().kafka_topics()
    await run_consumer(CONSUMER, [topics["order"]], handle)


if __name__ == "__main__":
    asyncio.run(main())
