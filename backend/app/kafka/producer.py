"""Kafka producer compatible with Aiven Inkless (no Kafka transactions)."""

from __future__ import annotations

import json
import logging
import ssl
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.core.config import Settings, get_settings
from app.kafka.envelope import EventEnvelope

logger = logging.getLogger(__name__)


def build_producer_config(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    ca = settings.resolve_path(settings.kafka_ssl_cafile)
    config: dict[str, Any] = {
        "bootstrap_servers": settings.kafka_bootstrap_servers,
        "client_id": settings.kafka_client_id,
        "security_protocol": settings.kafka_security_protocol,
        "sasl_mechanism": settings.kafka_sasl_mechanism,
        "sasl_plain_username": settings.kafka_sasl_username,
        "sasl_plain_password": settings.kafka_sasl_password,
        "value_serializer": lambda v: json.dumps(v).encode("utf-8"),
        "key_serializer": lambda k: k.encode("utf-8") if isinstance(k, str) else k,
        "acks": "all",
        # Inkless diskless topics: Kafka transactions are unsupported.
        "enable_idempotence": False,
    }
    if ca.exists():
        config["ssl_context"] = ssl.create_default_context(cafile=str(ca))
    return config


class KafkaProducer:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        settings = get_settings()
        if not settings.kafka_configured():
            logger.warning("Kafka is not configured; producer will remain idle.")
            return
        self._producer = AIOKafkaProducer(**build_producer_config(settings))
        await self._producer.start()
        logger.info("Kafka producer started (bootstrap host redacted).")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def publish(self, topic: str, event: EventEnvelope) -> None:
        if self._producer is None:
            raise RuntimeError("Kafka producer is not started")
        try:
            await self._producer.send_and_wait(
                topic,
                value=event.to_kafka_value(),
                key=event.aggregate_id,
            )
        except KafkaError as exc:
            logger.exception("Kafka publish failed for topic=%s event_type=%s", topic, event.event_type)
            raise RuntimeError("Kafka publish failed") from exc


producer = KafkaProducer()
