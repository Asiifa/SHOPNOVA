from __future__ import annotations

import asyncio
from uuid import UUID

from app.core.config import get_settings
from app.models.notification import Notification
from consumers.runtime import already_processed, mark_processed, run_consumer

CONSUMER = "notification-processor"


def handle(session, value: dict) -> None:
    event_type = value.get("event_type")
    if event_type not in {"order.created", "order.confirmed", "order.rejected"}:
        return
    event_id = UUID(value["event_id"])
    if already_processed(session, CONSUMER, event_id):
        return
    payload = value.get("payload") or {}
    order_number = payload.get("order_number", "")

    titles = {
        "order.created": "Order received",
        "order.confirmed": "Order confirmed",
        "order.rejected": "Order cancelled",
    }
    bodies = {
        "order.created": f"Order {order_number} has been received and is being processed.",
        "order.confirmed": f"Order {order_number} is confirmed. Stock has been reserved.",
        "order.rejected": f"Order {order_number} could not be fulfilled and was cancelled.",
    }
    session.add(
        Notification(
            customer_id=UUID(payload["customer_id"]) if payload.get("customer_id") else None,
            event_id=event_id,
            title=titles[event_type],
            body=bodies[event_type],
            channel="in_app",
        )
    )
    mark_processed(session, CONSUMER, event_id, event_type)


async def main() -> None:
    topics = get_settings().kafka_topics()
    await run_consumer(CONSUMER, [topics["order"]], handle)


if __name__ == "__main__":
    asyncio.run(main())
