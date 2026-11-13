from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, Page


class ProductOut(ORMModel):
    id: UUID
    name: str
    slug: str
    description: str
    sku: str
    category_id: UUID
    brand: str
    price: float
    discount_price: float | None
    city: str
    image_url: str
    specifications: dict
    rating: float
    review_count: int
    sold_count: int
    is_active: bool
    available_quantity: int = 0
    category_name: str | None = None
    category_slug: str | None = None
    images: list[str] = []


class ProductWrite(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=220)
    description: str
    sku: str = Field(min_length=3, max_length=40)
    category_id: UUID
    brand: str
    price: float = Field(gt=0)
    discount_price: float | None = None
    city: str
    image_url: str
    specifications: dict = Field(default_factory=dict)
    is_active: bool = True
    available_quantity: int = Field(default=0, ge=0)


class CategoryOut(ORMModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    image_url: str | None
    sort_order: int


class CategoryWrite(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    slug: str = Field(min_length=2, max_length=80)
    description: str | None = None
    image_url: str | None = None
    sort_order: int = 0
