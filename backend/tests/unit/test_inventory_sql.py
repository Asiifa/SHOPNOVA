import pytest

from app.services.order_service import concurrent_reserve_sql

pytestmark = pytest.mark.unit


def test_reservation_sql_is_conditional() -> None:
    sql = concurrent_reserve_sql()
    assert "available_quantity >= :qty" in sql
    assert "available_quantity = available_quantity - :qty" in sql
