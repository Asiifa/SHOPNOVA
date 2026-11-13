from pydantic import BaseModel, Field

from app.models.order import OrderStatus


class StatusBody(BaseModel):
    order_status: OrderStatus


class PatchInventory(BaseModel):
    available_quantity: int = Field(ge=0)
    reason: str = "admin_adjustment"
