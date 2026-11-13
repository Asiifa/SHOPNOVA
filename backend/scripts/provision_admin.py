"""Create an administrator from environment variables. Does not print the password."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database.session import get_session_factory  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


def main() -> int:
    settings = get_settings()
    email = (settings.admin_bootstrap_email or "").strip().lower()
    password = settings.admin_bootstrap_password
    if not email or not password:
        print("Set ADMIN_BOOTSTRAP_EMAIL and ADMIN_BOOTSTRAP_PASSWORD in backend/.env privately.")
        return 1
    session = get_session_factory()()
    try:
        existing = session.scalar(select(User).where(User.email == email))
        if existing:
            existing.role = UserRole.ADMIN
            existing.is_active = True
            session.commit()
            print("Administrator role ensured for existing account.")
            return 0
        session.add(
            User(
                email=email,
                full_name="SHOPNOVA Admin",
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
            )
        )
        session.commit()
        print("Administrator account created.")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
