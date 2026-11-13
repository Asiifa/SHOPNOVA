from __future__ import annotations

from datetime import datetime

from app.models.catalog import Product
from app.models.inventory import Inventory


def product_to_document(product: Product, inventory: Inventory | None) -> tuple[dict, int]:
    available = inventory.available_quantity if inventory else 0
    updated = product.updated_at or datetime.utcnow()
    version = int(updated.timestamp() * 1000)
    category_slug = product.category.slug if product.category else ""
    category_name = product.category.name if product.category else ""
    specs = product.specifications or {}
    spec_text = " ".join(f"{k} {v}" for k, v in specs.items())
    price = float(product.discount_price if product.discount_price is not None else product.price)
    document = {
        "product_id": str(product.id),
        "name": product.name,
        "description": product.description,
        "brand": product.brand,
        "category": category_name,
        "category_slug": category_slug,
        "price": price,
        "city": product.city,
        "specifications": spec_text,
        "available_quantity": available,
        "in_stock": available > 0 and product.is_active,
        "is_active": product.is_active,
        "rating": float(product.rating or 0),
        "sold_count": product.sold_count or 0,
        "image_url": product.image_url,
        "updated_at": updated.isoformat(),
    }
    return document, version
