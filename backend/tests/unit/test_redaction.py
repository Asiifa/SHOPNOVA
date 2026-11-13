import logging

import pytest

from app.core.logging import RedactingFormatter

pytestmark = pytest.mark.unit


def test_connection_string_password_redacted() -> None:
    formatter = RedactingFormatter("%(message)s")
    record = logging.LogRecord(
        "t", logging.INFO, __file__, 1, "postgresql+psycopg://user:supersecret@host/db", None, None
    )
    rendered = formatter.format(record)
    assert "supersecret" not in rendered
    assert "***" in rendered
