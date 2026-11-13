from uuid import UUID

from pydantic import BaseModel, Field

from app.models.order import PaymentMethod


class CartItemOut(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    brand: str
    image_url: str
    unit_price: float
    quantity: int
    available_quantity: int
    line_total: float


class CartOut(BaseModel):
    id: UUID
    items: list[CartItemOut]
    subtotal: float
    shipping: float
    total: float


class AddItemBody(BaseModel):
    product_id: UUID
    quantity: int = Field(default=1, ge=1, le=20)


class UpdateItemBody(BaseModel):
    quantity: int = Field(ge=1, le=20)


class PlaceOrderBody(BaseModel):
    address_id: UUID
    payment_method: PaymentMethod
