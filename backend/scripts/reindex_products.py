"""Full reindex from PostgreSQL into OpenSearch."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import joinedload  # noqa: E402

from app.database.session import get_session_factory  # noqa: E402
from app.models.catalog import Product  # noqa: E402
from app.opensearch.index import ensure_product_index  # noqa: E402
from app.opensearch.search import index_product_document  # noqa: E402
from app.services.product_document import product_to_document  # noqa: E402


def main() -> int:
    ensure_product_index()
    session = get_session_factory()()
    try:
        products = session.scalars(
            select(Product).options(joinedload(Product.category), joinedload(Product.inventory))
        ).unique().all()
        count = 0
        for product in products:
            document, version = product_to_document(product, product.inventory)
            index_product_document(document, version)
            count += 1
        print(f"Indexed {count} products into OpenSearch.")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
