import pytest

from app.kafka.envelope import EventEnvelope

pytestmark = pytest.mark.unit


def test_envelope_required_fields() -> None:
    event = EventEnvelope(event_type="OrderPlaced", aggregate_id="abc", payload={"n": 1})
    data = event.to_kafka_value()
    for key in ("event_id", "event_type", "event_version", "aggregate_id", "timestamp", "payload", "correlation_id"):
        assert key in data
    assert data["event_type"] == "OrderPlaced"
