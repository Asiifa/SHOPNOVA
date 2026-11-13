from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy.orm import joinedload

from app.core.config import get_settings
from app.models.catalog import Product
from app.models.inventory import Inventory
from app.opensearch.search import index_product_document, remove_product_document
from app.services.product_document import product_to_document
from consumers.runtime import already_processed, mark_processed, run_consumer

CONSUMER = "opensearch-indexer"


def handle(session, value: dict) -> None:
    event_type = value.get("event_type")
    if event_type not in {"product.created", "product.updated", "inventory.changed", "product.deleted"}:
        return
    event_id = UUID(value["event_id"])
    if already_processed(session, CONSUMER, event_id):
        return
    payload = value.get("payload") or {}

    if event_type == "product.deleted":
        product_id = str(payload.get("product_id") or value.get("aggregate_id") or "")
        if product_id:
            remove_product_document(product_id)
        mark_processed(session, CONSUMER, event_id, event_type)
        return

    product_id = UUID(payload.get("product_id") or value.get("aggregate_id"))
    product = (
        session.query(Product)
        .options(joinedload(Product.category), joinedload(Product.inventory))
        .get(product_id)
    )
    if not product:
        mark_processed(session, CONSUMER, event_id, event_type)
        return
    inventory = product.inventory or session.get(Inventory, product.id)
    document, version = product_to_document(product, inventory)
    index_product_document(document, version)
    mark_processed(session, CONSUMER, event_id, event_type)


async def main() -> None:
    topics = get_settings().kafka_topics()
    await run_consumer(CONSUMER, [topics["product"], topics["inventory"]], handle)


if __name__ == "__main__":
    asyncio.run(main())
