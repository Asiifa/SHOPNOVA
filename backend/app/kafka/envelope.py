from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_version: int = 1
    aggregate_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any]
    correlation_id: UUID = Field(default_factory=uuid4)

    def to_kafka_value(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        return data
