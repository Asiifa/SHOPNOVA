from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_admin
from app.models.catalog import Product
from app.models.inventory import Inventory, InventoryTransaction
from app.models.user import User
from app.schemas.admin import PatchInventory
from app.services.outbox import enqueue_event

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class InventoryOut(BaseModel):
    product_id: UUID
    name: str
    sku: str
    available_quantity: int
    reserved_quantity: int


@router.get("", response_model=list[InventoryOut])
def list_inventory(db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> list[InventoryOut]:
    rows = db.scalars(select(Inventory).options(joinedload(Inventory.product))).all()
    return [
        InventoryOut(
            product_id=r.product_id,
            name=r.product.name if r.product else "",
            sku=r.product.sku if r.product else "",
            available_quantity=r.available_quantity,
            reserved_quantity=r.reserved_quantity,
        )
        for r in rows
    ]


@router.patch("/{product_id}", response_model=InventoryOut)
def patch_inventory(
    product_id: UUID, body: PatchInventory, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> InventoryOut:
    inv = db.get(Inventory, product_id)
    product = db.get(Product, product_id)
    if not inv or not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inventory not found")
    delta = body.available_quantity - inv.available_quantity
    inv.available_quantity = body.available_quantity
    db.add(
        InventoryTransaction(
            product_id=product_id,
            change_type="ADJUST",
            quantity_delta=delta,
            reason=body.reason,
        )
    )
    enqueue_event(
        db,
        event_type="inventory.changed",
        aggregate_id=str(product_id),
        topic_key="inventory",
        payload={"product_id": str(product_id), "quantity_delta": delta, "reason": body.reason},
    )
    db.commit()
    return InventoryOut(
        product_id=product_id,
        name=product.name,
        sku=product.sku,
        available_quantity=inv.available_quantity,
        reserved_quantity=inv.reserved_quantity,
    )
