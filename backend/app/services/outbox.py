from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.kafka.envelope import EventEnvelope
from app.models.events import OutboxEvent


def enqueue_event(
    session: Session,
    *,
    event_type: str,
    aggregate_id: str,
    payload: dict,
    topic_key: str,
    correlation_id: UUID | None = None,
) -> OutboxEvent:
    topics = get_settings().kafka_topics()
    envelope = EventEnvelope(
        event_type=event_type,
        aggregate_id=aggregate_id,
        payload=payload,
        correlation_id=correlation_id or uuid4(),
    )
    row = OutboxEvent(
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        event_version=envelope.event_version,
        aggregate_id=envelope.aggregate_id,
        topic=topics[topic_key],
        payload=envelope.to_kafka_value(),
        correlation_id=envelope.correlation_id,
        published=False,
    )
    session.add(row)
    return row
