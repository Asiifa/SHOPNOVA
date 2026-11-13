from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.catalog import Category
from app.models.user import User
from app.schemas.common import ORMModel
from app.schemas.products import CategoryOut, CategoryWrite

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryOut]:
    rows = db.scalars(select(Category).where(Category.is_active.is_(True)).order_by(Category.sort_order)).all()
    return [CategoryOut.model_validate(row) for row in rows]


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryWrite, db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> CategoryOut:
    if db.scalar(select(Category).where(Category.slug == body.slug)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already exists")
    row = Category(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return CategoryOut.model_validate(row)
