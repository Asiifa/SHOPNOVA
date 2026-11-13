from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status

from app.core.config import get_settings

password_hasher = PasswordHasher()
Role = Literal["CUSTOMER", "ADMIN"]


def hash_password(plain: str) -> str:
    return password_hasher.hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, plain)
    except VerifyMismatchError:
        return False


def create_token(subject: str, role: Role, token_type: str, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "typ": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_access_token(user_id: UUID, role: Role) -> str:
    minutes = get_settings().access_token_expire_minutes
    return create_token(str(user_id), role, "access", timedelta(minutes=minutes))


def create_refresh_token(user_id: UUID, role: Role) -> str:
    days = get_settings().refresh_token_expire_days
    return create_token(str(user_id), role, "refresh", timedelta(days=days))


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
    if payload.get("typ") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
    return payload
