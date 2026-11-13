from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import CustomerAddress, User
from app.schemas.common import ORMModel

router = APIRouter(prefix="/api/addresses", tags=["addresses"])


class AddressWrite(BaseModel):
    label: str = "Home"
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=10, max_length=20)
    line1: str = Field(min_length=4, max_length=255)
    line2: str | None = None
    city: str
    state: str
    pin_code: str = Field(min_length=6, max_length=10)
    is_default: bool = False


class AddressOut(ORMModel):
    id: UUID
    label: str
    full_name: str
    phone: str
    line1: str
    line2: str | None
    city: str
    state: str
    pin_code: str
    is_default: bool


@router.get("", response_model=list[AddressOut])
def list_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[AddressOut]:
    rows = db.scalars(select(CustomerAddress).where(CustomerAddress.customer_id == user.id)).all()
    return [AddressOut.model_validate(r) for r in rows]


@router.post("", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(body: AddressWrite, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> AddressOut:
    row = CustomerAddress(customer_id=user.id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return AddressOut.model_validate(row)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    row = db.get(CustomerAddress, address_id)
    if not row or row.customer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Address not found")
    db.delete(row)
    db.commit()
