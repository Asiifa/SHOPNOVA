"""Check Aiven connectivity without printing secrets."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging  # noqa: E402


def _status(ok: bool) -> str:
    return "ok" if ok else "failed"


def check_postgres(settings) -> tuple[bool, str]:
    if not settings.postgres_configured():
        return False, "not_configured"
    if settings.postgres_sslmode in {"verify-full", "verify-ca"} and not settings.ca_path.exists():
        return False, "ca_missing"
    from sqlalchemy import text

    from app.database.session import get_engine

    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True, "reachable"


def check_kafka(settings) -> tuple[bool, str]:
    if not settings.kafka_configured():
        return False, "not_configured"
    ca = settings.resolve_path(settings.kafka_ssl_cafile)
    if not ca.exists():
        return False, "ca_missing"
    import asyncio

    from aiokafka import AIOKafkaProducer

    from app.kafka.producer import build_producer_config

    async def _probe() -> list[str]:
        producer = AIOKafkaProducer(**build_producer_config(settings))
        await producer.start()
        try:
            return sorted(producer.client.cluster.topics())
        finally:
            await producer.stop()

    topics = asyncio.run(_probe())
    expected = set(settings.kafka_topics().values())
    missing = sorted(expected - set(topics))
    if missing:
        return True, f"reachable; missing_topics={len(missing)}"
    return True, "reachable"


def check_opensearch(settings) -> tuple[bool, str]:
    if not settings.opensearch_configured():
        return False, "not_configured"
    from app.opensearch.client import get_opensearch_client

    client = get_opensearch_client()
    info = client.info()
    version = info.get("version", {}).get("number", "unknown")
    return True, f"reachable; version={version}"


def main() -> int:
    configure_logging(False)
    settings = get_settings()
    print("SHOPNOVA service verification (secrets redacted)")
    print(f"postgres service: {settings.aiven_pg_service}")
    pg_ok, pg_detail = check_postgres(settings)
    print(f"postgres: {_status(pg_ok)} ({pg_detail})")

    print(f"kafka service: {settings.aiven_kafka_service}")
    try:
        k_ok, k_detail = check_kafka(settings)
    except Exception:
        k_ok, k_detail = False, "unreachable"
    print(f"kafka: {_status(k_ok)} ({k_detail})")

    print(f"opensearch service: {settings.aiven_os_service}")
    try:
        o_ok, o_detail = check_opensearch(settings)
    except Exception:
        o_ok, o_detail = False, "unreachable"
    print(f"opensearch: {_status(o_ok)} ({o_detail})")

    return 0 if pg_ok and k_ok and o_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
