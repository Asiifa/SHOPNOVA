from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RefreshRequest, TokenPair, UserPublic
from app.services.auth_service import authenticate, register_customer, to_public

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> UserPublic:
    user = register_customer(
        db, email=body.email, password=body.password, full_name=body.full_name, phone=body.phone
    )
    return to_public(user)


@router.post("/login", response_model=TokenPair)
@limiter.limit(lambda: get_settings().rate_limit_login)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    return authenticate(db, email=body.email, password=body.password)


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    payload = decode_token(body.refresh_token, "refresh")
    user = db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return TokenPair(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id, user.role.value),
    )


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> UserPublic:
    return to_public(user)
