from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class Message(BaseModel):
    detail: str


class HealthService(BaseModel):
    name: str
    identifier: str | None = None
    configured: bool
    reachable: bool | None = None
    detail: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublic(ORMModel):
    id: UUID
    email: str
    full_name: str
    phone: str | None
    role: str
    created_at: datetime
