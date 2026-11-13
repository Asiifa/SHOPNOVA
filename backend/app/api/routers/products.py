from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_admin
from app.models.catalog import Category, Product, ProductImage
from app.models.inventory import Inventory
from app.models.user import User
from app.schemas.common import ORMModel, Page
from app.schemas.products import ProductOut, ProductWrite
from app.services.outbox import enqueue_event

router = APIRouter(prefix="/api/products", tags=["products"])


def _to_out(product: Product) -> ProductOut:
    qty = product.inventory.available_quantity if product.inventory else 0
    return ProductOut(
        id=product.id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        sku=product.sku,
        category_id=product.category_id,
        brand=product.brand,
        price=float(product.price),
        discount_price=float(product.discount_price) if product.discount_price is not None else None,
        city=product.city,
        image_url=product.image_url,
        specifications=product.specifications or {},
        rating=float(product.rating or 0),
        review_count=product.review_count,
        sold_count=product.sold_count,
        is_active=product.is_active,
        available_quantity=qty,
        category_name=product.category.name if product.category else None,
        category_slug=product.category.slug if product.category else None,
        images=[img.url for img in (product.images or [])] or [product.image_url],
    )


@router.get("", response_model=Page[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
    category: str | None = None,
    brand: str | None = None,
    featured: bool | None = None,
    sort: str = "newest",
) -> Page[ProductOut]:
    stmt = (
        select(Product)
        .options(joinedload(Product.inventory), joinedload(Product.category), joinedload(Product.images))
        .where(Product.is_active.is_(True))
    )
    if category:
        stmt = stmt.join(Category).where(Category.slug == category)
    if brand:
        stmt = stmt.where(Product.brand == brand)
    if sort == "price_asc":
        stmt = stmt.order_by(func.coalesce(Product.discount_price, Product.price).asc())
    elif sort == "price_desc":
        stmt = stmt.order_by(func.coalesce(Product.discount_price, Product.price).desc())
    elif sort == "popularity":
        stmt = stmt.order_by(Product.sold_count.desc())
    else:
        stmt = stmt.order_by(Product.created_at.desc())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size).execution_options(populate_existing=True)).unique().all()
    return Page(items=[_to_out(p) for p in items], total=total, page=page, page_size=page_size)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: UUID, db: Session = Depends(get_db)) -> ProductOut:
    product = db.scalar(
        select(Product)
        .options(joinedload(Product.inventory), joinedload(Product.category), joinedload(Product.images))
        .where(Product.id == product_id)
    )
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return _to_out(product)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(body: ProductWrite, db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> ProductOut:
    if db.scalar(select(Product).where(Product.sku == body.sku)):
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already exists")
    product = Product(
        name=body.name,
        slug=body.slug,
        description=body.description,
        sku=body.sku,
        category_id=body.category_id,
        brand=body.brand,
        price=body.price,
        discount_price=body.discount_price,
        city=body.city,
        image_url=body.image_url,
        specifications=body.specifications,
        is_active=body.is_active,
    )
    db.add(product)
    db.flush()
    db.add(Inventory(product_id=product.id, available_quantity=body.available_quantity, reserved_quantity=0))
    db.add(ProductImage(product_id=product.id, url=body.image_url, sort_order=0))
    enqueue_event(
        db,
        event_type="product.created",
        aggregate_id=str(product.id),
        topic_key="product",
        payload={"product_id": str(product.id), "name": product.name, "sku": product.sku},
    )
    db.commit()
    db.refresh(product)
    product = db.scalar(
        select(Product)
        .options(joinedload(Product.inventory), joinedload(Product.category), joinedload(Product.images))
        .where(Product.id == product.id)
    )
    return _to_out(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: UUID, body: ProductWrite, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> ProductOut:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    for field, value in body.model_dump(exclude={"available_quantity"}).items():
        setattr(product, field, value)
    if product.inventory:
        product.inventory.available_quantity = body.available_quantity
    enqueue_event(
        db,
        event_type="product.updated",
        aggregate_id=str(product.id),
        topic_key="product",
        payload={"product_id": str(product.id), "name": product.name, "is_active": product.is_active},
    )
    db.commit()
    product = db.scalar(
        select(Product)
        .options(joinedload(Product.inventory), joinedload(Product.category), joinedload(Product.images))
        .where(Product.id == product_id)
    )
    return _to_out(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_product(product_id: UUID, db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> None:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    product.is_active = False
    enqueue_event(
        db,
        event_type="product.deleted",
        aggregate_id=str(product.id),
        topic_key="product",
        payload={"product_id": str(product.id), "name": product.name, "is_active": False},
    )
    db.commit()
