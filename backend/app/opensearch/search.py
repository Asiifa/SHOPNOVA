from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.opensearch.client import get_opensearch_client
from app.opensearch.index import ensure_product_index


def build_search_body(
    q: str | None,
    *,
    category: str | None = None,
    brand: str | None = None,
    city: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
    sort: str = "relevance",
    page: int = 1,
    page_size: int = 12,
) -> dict[str, Any]:
    filters: list[dict[str, Any]] = [{"term": {"is_active": True}}]
    if category:
        filters.append({"term": {"category_slug": category}})
    if brand:
        filters.append({"term": {"brand.keyword": brand}})
    if city:
        filters.append({"term": {"city": city}})
    if in_stock is True:
        filters.append({"term": {"in_stock": True}})
    if min_price is not None or max_price is not None:
        rng: dict[str, Any] = {}
        if min_price is not None:
            rng["gte"] = min_price
        if max_price is not None:
            rng["lte"] = max_price
        filters.append({"range": {"price": rng}})

    must: list[dict[str, Any]]
    if q and q.strip():
        must = [
            {
                "multi_match": {
                    "query": q.strip(),
                    "fields": ["name^4", "name.autocomplete^2", "brand^3", "description", "specifications"],
                    "fuzziness": "AUTO",
                    "prefix_length": 1,
                    "operator": "or",
                    "type": "best_fields",
                }
            }
        ]
    else:
        must = [{"match_all": {}}]

    sort_clause: list[Any]
    if sort == "price_asc":
        sort_clause = [{"price": "asc"}]
    elif sort == "price_desc":
        sort_clause = [{"price": "desc"}]
    elif sort == "newest":
        sort_clause = [{"updated_at": "desc"}]
    elif sort == "popularity":
        sort_clause = [{"sold_count": "desc"}]
    else:
        sort_clause = ["_score", {"sold_count": "desc"}]

    return {
        "from": (page - 1) * page_size,
        "size": page_size,
        "query": {"bool": {"must": must, "filter": filters}},
        "sort": sort_clause,
        "track_total_hits": True,
    }


def search_products(**kwargs: Any) -> dict[str, Any]:
    ensure_product_index()
    client = get_opensearch_client()
    index = get_settings().opensearch_index
    body = build_search_body(**kwargs)
    return client.search(index=index, body=body)


def suggest_products(q: str, size: int = 8) -> list[dict[str, Any]]:
    ensure_product_index()
    client = get_opensearch_client()
    index = get_settings().opensearch_index
    body = {
        "size": size,
        "query": {
            "bool": {
                "filter": [{"term": {"is_active": True}}],
                "must": [
                    {
                        "multi_match": {
                            "query": q,
                            "fields": ["name.autocomplete^3", "name^2", "brand"],
                            "fuzziness": "AUTO",
                            "type": "bool_prefix",
                        }
                    }
                ],
            }
        },
        "_source": ["product_id", "name", "brand", "price", "image_url"],
    }
    result = client.search(index=index, body=body)
    return [hit["_source"] for hit in result.get("hits", {}).get("hits", [])]


def index_product_document(document: dict[str, Any], version: int) -> None:
    ensure_product_index()
    client = get_opensearch_client()
    index = get_settings().opensearch_index
    product_id = document["product_id"]
    existing = client.get(index=index, id=product_id, ignore=[404])
    if existing and existing.get("found"):
        current = existing["_source"].get("version", 0)
        if version < current:
            return
    client.index(index=index, id=product_id, body={**document, "version": version}, refresh=False)


def remove_product_document(product_id: str) -> None:
    ensure_product_index()
    client = get_opensearch_client()
    index = get_settings().opensearch_index
    client.delete(index=index, id=product_id, ignore=[404], refresh=False)
