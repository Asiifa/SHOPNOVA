"""Idempotent catalogue seed. Uses fictional products and customers only."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database.session import get_session_factory  # noqa: E402
from app.models.catalog import Category, Product, ProductImage  # noqa: E402
from app.models.inventory import Inventory  # noqa: E402
from app.models.user import CustomerAddress, User, UserRole  # noqa: E402
from app.services.outbox import enqueue_event  # noqa: E402
from scripts.catalog_data import CATEGORIES, PRODUCTS  # noqa: E402


def seed_catalog(session_factory) -> int:
    """Idempotently seed categories, products, inventory and a demo customer.

    Safe to run repeatedly: existing categories/products/users are detected by
    slug/sku/email and left untouched.
    """
    session = session_factory()
    try:
        slug_to_id: dict[str, object] = {}
        for index, cat in enumerate(CATEGORIES):
            row = session.scalar(select(Category).where(Category.slug == cat["slug"]))
            if not row:
                row = Category(
                    name=cat["name"],
                    slug=cat["slug"],
                    description=cat["description"],
                    image_url=cat["image_url"],
                    sort_order=index,
                )
                session.add(row)
                session.flush()
            slug_to_id[cat["slug"]] = row.id

        for item in PRODUCTS:
            existing = session.scalar(select(Product).where(Product.sku == item["sku"]))
            if existing:
                continue
            product = Product(
                name=item["name"],
                slug=item["slug"],
                description=item["description"],
                sku=item["sku"],
                category_id=slug_to_id[item["category"]],
                brand=item["brand"],
                price=Decimal(str(item["price"])),
                discount_price=Decimal(str(item["discount_price"])) if item["discount_price"] else None,
                city=item["city"],
                image_url=item["image"],
                specifications=item["specifications"],
                rating=Decimal("4.40"),
                review_count=24,
                is_active=True,
            )
            session.add(product)
            session.flush()
            session.add(ProductImage(product_id=product.id, url=item["image"], alt_text=item["name"]))
            session.add(Inventory(product_id=product.id, available_quantity=item["stock"], reserved_quantity=0))
            enqueue_event(
                session,
                event_type="ProductCreated",
                aggregate_id=str(product.id),
                topic_key="product",
                payload={"product_id": str(product.id), "sku": product.sku, "name": product.name},
            )

        demo = session.scalar(select(User).where(User.email == "priya.demo@shopnova.test"))
        if not demo:
            demo = User(
                email="priya.demo@shopnova.test",
                full_name="Priya Sharma",
                phone="9876500001",
                password_hash=hash_password("DemoPass123"),
                role=UserRole.CUSTOMER,
            )
            session.add(demo)
            session.flush()
            session.add(
                CustomerAddress(
                    customer_id=demo.id,
                    label="Home",
                    full_name="Priya Sharma",
                    phone="9876500001",
                    line1="12, Maple Residency",
                    line2="Koramangala 5th Block",
                    city="Bengaluru",
                    state="Karnataka",
                    pin_code="560095",
                    is_default=True,
                )
            )
        session.commit()
        print(f"Seed complete. Categories={len(CATEGORIES)} catalogue_skus={len(PRODUCTS)}")
        return len(PRODUCTS)
    finally:
        session.close()


def main() -> int:
    factory = get_session_factory()
    if factory is None:
        print(
            "No database configured. Set POSTGRES_* in backend/.env, or start the API "
            "in dev mode (SQLite fallback) so the catalogue can be seeded."
        )
        return 1
    seed_catalog(factory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
