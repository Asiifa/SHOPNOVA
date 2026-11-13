from __future__ import annotations

import asyncio
import json
import logging
import signal
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from aiokafka import AIOKafkaConsumer
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import get_session_factory
from app.kafka.producer import build_producer_config, producer
from app.models.events import ProcessedEvent

logger = logging.getLogger(__name__)


def consumer_config(group_id: str) -> dict:
    settings = get_settings()
    base = build_producer_config(settings)
    base.pop("value_serializer", None)
    base.pop("key_serializer", None)
    base.pop("acks", None)
    base.pop("enable_idempotence", None)
    base.update(
        {
            "group_id": group_id,
            "enable_auto_commit": False,
            "auto_offset_reset": "earliest",
            "value_deserializer": lambda v: json.loads(v.decode("utf-8")),
            "key_deserializer": lambda k: k.decode("utf-8") if k else None,
            "client_id": f"{settings.kafka_client_id}-{group_id}",
        }
    )
    return base


def already_processed(session, consumer_name: str, event_id: UUID) -> bool:
    row = session.query(ProcessedEvent).filter_by(consumer_name=consumer_name, event_id=event_id).first()
    return row is not None


def mark_processed(session, consumer_name: str, event_id: UUID, event_type: str) -> None:
    stmt = pg_insert(ProcessedEvent).values(
        consumer_name=consumer_name, event_id=event_id, event_type=event_type
    )
    dialect = session.get_bind().dialect.name
    if dialect == "sqlite":
        stmt = stmt.on_conflict_do_nothing(index_elements=["consumer_name", "event_id"])
    else:
        stmt = stmt.on_conflict_do_nothing(constraint="uq_processed_consumer_event")
    session.execute(stmt)


async def _send_to_dlq(value: dict, exc: str) -> None:
    settings = get_settings()
    dlq_topic = settings.kafka_topics()["dlq"]
    try:
        if producer._producer is None:
            await producer.start()
        await producer.publish(
            dlq_topic,
            {
                "original_value": value,
                "failure_reason": exc,
                "failed_at": datetime.now(UTC).isoformat(),
            },
            key=str(value.get("event_id") or "unknown"),
        )
        logger.error("Message dead-lettered to %s: %s", dlq_topic, exc[:200])
    except Exception:
        logger.exception("Failed to dead-letter message")


async def run_consumer(group_id: str, topics: list[str], handler: Callable) -> None:
    settings = get_settings()
    configure_logging(settings.app_debug)
    if not settings.kafka_configured():
        logger.warning("Consumer %s idle: Kafka is not configured in backend/.env", group_id)
        return
    stop = asyncio.Event()

    def _stop(*_args: object) -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_: stop.set())

    consumer = AIOKafkaConsumer(*topics, **consumer_config(group_id))
    await consumer.start()
    logger.info("Consumer %s started for %s topics", group_id, topics)
    factory = get_session_factory()
    try:
        while not stop.is_set():
            batch = await consumer.getmany(timeout_ms=settings.consumer_poll_timeout_ms, max_records=20)
            if not batch:
                continue
            for _tp, messages in batch.items():
                for msg in messages:
                    event_type = (msg.value or {}).get("event_type")
                    session = factory()
                    try:
                        handler(session, msg.value)
                        session.commit()
                        logger.debug("Consumer %s processed event_type=%s", group_id, event_type)
                    except Exception:
                        session.rollback()
                        logger.exception(
                            "Consumer %s failed on event_type=%s; dead-lettering and advancing offset",
                            group_id,
                            event_type,
                        )
                        await _send_to_dlq(msg.value or {}, "handler_failure")
                    finally:
                        session.close()
            # Commit offsets only after every message in the batch has been
            # persisted to PostgreSQL (or dead-lettered). Never commit before
            # the corresponding database transaction succeeds.
            await consumer.commit()
    finally:
        await consumer.stop()
        logger.info("Consumer %s stopped", group_id)
