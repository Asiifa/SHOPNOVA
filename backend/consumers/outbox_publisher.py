"""Publish committed outbox rows to Kafka. Kafka transactions are intentionally unused (Inkless).

Reliability contract:
- Rows are published at-least-once. A row is marked `published` only after the
  Kafka ack arrives.
- Transient failures increment `publish_attempts` and are retried on the next
  poll cycle.
- After MAX_PUBLISH_ATTEMPTS failures the event is forwarded to the dead-letter
  topic (`shopnova.dead-letter-events`) with the original payload and the last
  error, then marked published so it is never retried endlessly. Failed events
  are never silently discarded.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import get_session_factory
from app.kafka.envelope import EventEnvelope
from app.kafka.producer import producer
from app.models.events import OutboxEvent

logger = logging.getLogger(__name__)

MAX_PUBLISH_ATTEMPTS = 12
BATCH_SIZE = 50


async def publish_once() -> int:
    factory = get_session_factory()
    session = factory()
    published = 0
    dlq = 0
    try:
        rows = session.scalars(
            select(OutboxEvent)
            .where(OutboxEvent.published.is_(False), OutboxEvent.publish_attempts < MAX_PUBLISH_ATTEMPTS)
            .order_by(OutboxEvent.created_at.asc())
            .limit(BATCH_SIZE)
        ).all()
        for row in rows:
            try:
                event = EventEnvelope.model_validate(row.payload)
                await producer.publish(row.topic, event)
                row.published = True
                row.published_at = datetime.now(UTC)
                row.last_error = None
                published += 1
            except Exception as exc:
                row.publish_attempts += 1
                row.last_error = str(exc)[:480]
                logger.warning(
                    "Outbox publish failed event_type=%s attempts=%s error=%s",
                    row.event_type,
                    row.publish_attempts,
                    row.last_error,
                )
                if row.publish_attempts >= MAX_PUBLISH_ATTEMPTS:
                    try:
                        settings = get_settings()
                        await producer.publish(
                            settings.kafka_topics()["dlq"],
                            EventEnvelope(
                                event_type=f"{row.event_type}.dlq",
                                aggregate_id=row.aggregate_id,
                                payload={
                                    "original_topic": row.topic,
                                    "original_event_type": row.event_type,
                                    "original_payload": row.payload,
                                    "last_error": row.last_error,
                                    "failed_at": datetime.now(UTC).isoformat(),
                                },
                                correlation_id=row.correlation_id,
                            ),
                        )
                        dlq += 1
                        row.published = True
                        row.published_at = datetime.now(UTC)
                        logger.error(
                            "Event %s moved to dead-letter topic after %s attempts",
                            row.event_id,
                            row.publish_attempts,
                        )
                    except Exception as dlq_exc:
                        logger.exception("Dead-letter publish failed for event %s", row.event_id)
        session.commit()
    finally:
        session.close()
    if published or dlq:
        logger.info("Outbox cycle: published=%s dead-lettered=%s", published, dlq)
    return published + dlq


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_debug)
    if not settings.kafka_configured() or not settings.postgres_configured():
        logger.warning("Outbox publisher idle: PostgreSQL and Kafka must be configured in backend/.env")
        return
    await producer.start()
    try:
        while True:
            await publish_once()
            await asyncio.sleep(settings.outbox_poll_interval_seconds)
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
