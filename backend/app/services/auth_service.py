from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.cart import Cart
from app.models.user import User, UserRole
from app.schemas.common import TokenPair, UserPublic

PASSWORD_RULE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


def register_customer(session: Session, *, email: str, password: str, full_name: str, phone: str | None) -> User:
    if not PASSWORD_RULE.match(password):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Password must be at least 8 characters and include a letter and a number.",
        )
    existing = session.scalar(select(User).where(User.email == email.lower()))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    user = User(
        email=email.lower(),
        full_name=full_name.strip(),
        phone=phone,
        password_hash=hash_password(password),
        role=UserRole.CUSTOMER,
    )
    session.add(user)
    session.flush()
    session.add(Cart(customer_id=user.id))
    session.commit()
    session.refresh(user)
    return user


def authenticate(session: Session, *, email: str, password: str) -> TokenPair:
    user = session.scalar(select(User).where(User.email == email.lower()))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
    return TokenPair(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id, user.role.value),
    )


def to_public(user: User) -> UserPublic:
    return UserPublic.model_validate(user)
