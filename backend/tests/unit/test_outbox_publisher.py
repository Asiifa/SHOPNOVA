"""Unit tests for the outbox publisher with a fake Kafka producer."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.session import get_session_factory
from app.models.events import OutboxEvent
from consumers import outbox_publisher

pytestmark = pytest.mark.unit


class FakeProducer:
    def __init__(self, *, fail_real: bool = False) -> None:
        self.published: list[tuple[str, dict]] = []
        self.fail_real = fail_real

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def publish(self, topic: str, event) -> None:
        if self.fail_real and not topic.endswith("dead-letter-events"):
            raise RuntimeError("kafka down")
        self.published.append((topic, event))


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    outbox_publisher.get_session_factory = lambda: factory
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


def _make_event(session, *, event_type="order.created", topic="shopnova.order-events", attempts=0):
    from app.kafka.envelope import EventEnvelope

    envelope = EventEnvelope(
        event_type=event_type,
        aggregate_id="order-1",
        payload={"order_id": "order-1"},
        correlation_id=uuid4(),
    )
    row = OutboxEvent(
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        aggregate_id=envelope.aggregate_id,
        topic=topic,
        payload=envelope.to_kafka_value(),
        correlation_id=envelope.correlation_id,
        published=False,
        publish_attempts=attempts,
    )
    session.add(row)
    session.commit()
    return row


@pytest.mark.asyncio
async def test_publish_once_marks_rows_published(session):
    fake = FakeProducer()
    _make_event(session)
    with patch.object(outbox_publisher, "producer", fake):
        published = await outbox_publisher.publish_once()
    assert published == 1
    assert len(fake.published) == 1
    assert fake.published[0][0] == "shopnova.order-events"
    row = session.query(OutboxEvent).one()
    assert row.published is True
    assert row.published_at is not None


@pytest.mark.asyncio
async def test_repeated_failures_go_to_dlq(session):
    fake = FakeProducer(fail_real=True)
    _make_event(session, attempts=11)  # next attempt hits the limit
    with patch.object(outbox_publisher, "producer", fake):
        published = await outbox_publisher.publish_once()
    assert published == 1
    # One failed real attempt is not recorded as published; the dead-letter
    # publish succeeds and the row is marked published.
    assert len(fake.published) == 1
    assert fake.published[0][0] == "shopnova.dead-letter-events"
    row = session.query(OutboxEvent).one()
    assert row.published is True
    assert row.last_error is not None
