"""Concurrent purchase test against Aiven PostgreSQL.

Skipped until credentials are configured. When run, two sessions attempt to
buy the last unit; exactly one UPDATE ... WHERE available_quantity >= qty succeeds.
"""

from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.database.session import get_session_factory

pytestmark = pytest.mark.integration


def _buy(product_id: str, qty: int) -> bool:
    session = get_session_factory()()
    try:
        result = session.execute(
            text(
                """
                UPDATE inventory
                SET available_quantity = available_quantity - :qty,
                    reserved_quantity = reserved_quantity + :qty
                WHERE product_id = CAST(:product_id AS uuid)
                  AND available_quantity >= :qty
                RETURNING product_id
                """
            ),
            {"product_id": product_id, "qty": qty},
        )
        row = result.first()
        session.commit()
        return row is not None
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_last_unit_sold_once() -> None:
    settings = get_settings()
    if not settings.postgres_configured():
        pytest.skip("PostgreSQL is not configured")
    session = get_session_factory()()
    try:
        product_id = session.execute(text("SELECT product_id FROM inventory LIMIT 1")).scalar()
        if not product_id:
            pytest.skip("No inventory rows; seed the catalogue first")
        session.execute(
            text("UPDATE inventory SET available_quantity = 1, reserved_quantity = 0 WHERE product_id = :id"),
            {"id": product_id},
        )
        session.commit()
    finally:
        session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: _buy(str(product_id), 1), range(2)))

    assert sorted(results) == [False, True]
    session = get_session_factory()()
    try:
        remaining = session.execute(
            text("SELECT available_quantity FROM inventory WHERE product_id = :id"),
            {"id": product_id},
        ).scalar()
        assert remaining == 0
    finally:
        session.close()
