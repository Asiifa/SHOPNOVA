import pytest

from app.core.security import hash_password, verify_password

pytestmark = pytest.mark.unit


def test_password_hash_is_not_plaintext() -> None:
    hashed = hash_password("DemoPass123")
    assert hashed != "DemoPass123"
    assert hashed.startswith("$argon2")
    assert verify_password("DemoPass123", hashed)
    assert not verify_password("wrong-password", hashed)
