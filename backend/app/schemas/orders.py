from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    product_name: str
    sku: str
    unit_price: float
    quantity: int
    line_total: float


class OrderOut(BaseModel):
    id: UUID
    order_number: str
    total_amount: float
    shipping_amount: float
    payment_method: str
    payment_status: str
    order_status: str
    created_at: datetime
    items: list[OrderItemOut]
