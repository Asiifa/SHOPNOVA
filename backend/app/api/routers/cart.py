from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.cart import Cart, CartItem
from app.models.catalog import Product
from app.models.user import User
from app.schemas.cart import AddItemBody, CartOut, UpdateItemBody

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _ensure_cart(db: Session, user: User) -> Cart:
    cart = db.scalar(select(Cart).where(Cart.customer_id == user.id).options(joinedload(Cart.items)))
    if not cart:
        cart = Cart(customer_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def _serialize(db: Session, cart: Cart) -> CartOut:
    items_out = []
    subtotal = 0.0
    for item in cart.items:
        product = db.get(Product, item.product_id)
        if not product:
            continue
        price = float(product.discount_price if product.discount_price is not None else product.price)
        qty_avail = product.inventory.available_quantity if product.inventory else 0
        line = price * item.quantity
        subtotal += line
        items_out.append(
            {
                "id": item.id,
                "product_id": product.id,
                "name": product.name,
                "brand": product.brand,
                "image_url": product.image_url,
                "unit_price": price,
                "quantity": item.quantity,
                "available_quantity": qty_avail,
                "line_total": round(line, 2),
            }
        )
    shipping = 0.0 if subtotal >= 999 else (49.0 if items_out else 0.0)
    return CartOut(
        id=cart.id,
        items=items_out,
        subtotal=round(subtotal, 2),
        shipping=shipping,
        total=round(subtotal + shipping, 2),
    )


@router.get("", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CartOut:
    cart = _ensure_cart(db, user)
    cart = db.scalar(select(Cart).where(Cart.id == cart.id).options(joinedload(Cart.items)))
    return _serialize(db, cart)


@router.post("/items", response_model=CartOut)
def add_item(body: AddItemBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CartOut:
    product = db.get(Product, body.product_id)
    if not product or not product.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    available = product.inventory.available_quantity if product.inventory else 0
    if available < body.quantity:
        raise HTTPException(status.HTTP_409_CONFLICT, "Insufficient stock")
    cart = _ensure_cart(db, user)
    existing = next((i for i in cart.items if i.product_id == body.product_id), None)
    if existing:
        new_qty = existing.quantity + body.quantity
        if new_qty > available:
            raise HTTPException(status.HTTP_409_CONFLICT, "Insufficient stock")
        existing.quantity = new_qty
    else:
        db.add(CartItem(cart_id=cart.id, product_id=body.product_id, quantity=body.quantity))
    db.commit()
    cart = db.scalar(select(Cart).where(Cart.id == cart.id).options(joinedload(Cart.items)))
    return _serialize(db, cart)


@router.put("/items/{item_id}", response_model=CartOut)
def update_item(
    item_id: UUID, body: UpdateItemBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> CartOut:
    cart = _ensure_cart(db, user)
    item = db.get(CartItem, item_id)
    if not item or item.cart_id != cart.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cart item not found")
    product = db.get(Product, item.product_id)
    available = product.inventory.available_quantity if product and product.inventory else 0
    if body.quantity > available:
        raise HTTPException(status.HTTP_409_CONFLICT, "Insufficient stock")
    item.quantity = body.quantity
    db.commit()
    cart = db.scalar(select(Cart).where(Cart.id == cart.id).options(joinedload(Cart.items)))
    return _serialize(db, cart)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(item_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CartOut:
    cart = _ensure_cart(db, user)
    item = db.get(CartItem, item_id)
    if not item or item.cart_id != cart.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cart item not found")
    db.delete(item)
    db.commit()
    cart = db.scalar(select(Cart).where(Cart.id == cart.id).options(joinedload(Cart.items)))
    return _serialize(db, cart)
