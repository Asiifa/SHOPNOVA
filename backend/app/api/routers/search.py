from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import get_settings
from app.opensearch.search import search_products, suggest_products

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search(
    q: str | None = Query(default=None, max_length=200),
    category: str | None = None,
    brand: str | None = None,
    city: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    in_stock: bool | None = None,
    sort: str = Query(default="relevance"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
) -> dict:
    if not get_settings().opensearch_configured():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OpenSearch is not configured. Complete private Aiven setup before searching.",
        )
    try:
        result = search_products(
            q=q,
            category=category,
            brand=brand,
            city=city,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            sort=sort,
            page=page,
            page_size=page_size,
        )
    except Exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Search service is unavailable.") from None
    hits = result.get("hits", {})
    total = hits.get("total", {}).get("value", 0)
    items = []
    for hit in hits.get("hits", []):
        src = hit["_source"]
        items.append(
            {
                "id": src.get("product_id"),
                "name": src.get("name"),
                "brand": src.get("brand"),
                "price": src.get("price"),
                "city": src.get("city"),
                "image_url": src.get("image_url"),
                "available_quantity": src.get("available_quantity"),
                "in_stock": src.get("in_stock"),
                "rating": src.get("rating"),
                "category": src.get("category"),
                "category_slug": src.get("category_slug"),
                "score": hit.get("_score"),
            }
        )
    return {"items": items, "total": total, "page": page, "page_size": page_size, "engine": "opensearch"}


@router.get("/suggestions")
def suggestions(q: str = Query(min_length=2, max_length=80)) -> dict:
    if not get_settings().opensearch_configured():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "OpenSearch is not configured.")
    try:
        return {"items": suggest_products(q)}
    except Exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Search service is unavailable.") from None
