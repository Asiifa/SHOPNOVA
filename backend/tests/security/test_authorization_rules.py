import pytest
from fastapi import HTTPException

from app.api.deps import require_admin
from app.models.user import User, UserRole

pytestmark = pytest.mark.security


def test_customer_cannot_pass_admin_guard() -> None:
    user = User(email="a@b.c", full_name="A", password_hash="x", role=UserRole.CUSTOMER)
    with pytest.raises(HTTPException) as exc:
        require_admin(user)
    assert exc.value.status_code == 403


def test_admin_passes_guard() -> None:
    user = User(email="admin@b.c", full_name="A", password_hash="x", role=UserRole.ADMIN)
    assert require_admin(user) is user
