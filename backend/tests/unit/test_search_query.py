import pytest

from app.opensearch.search import build_search_body

pytestmark = pytest.mark.unit


def test_fuzzy_query_includes_fuzziness() -> None:
    body = build_search_body("bluetoth hedphones")
    match = body["query"]["bool"]["must"][0]["multi_match"]
    assert match["fuzziness"] == "AUTO"
    assert "name" in match["fields"][0]


def test_filters_and_price_sort() -> None:
    body = build_search_body(
        None,
        category="electronics",
        min_price=500,
        max_price=3000,
        in_stock=True,
        sort="price_asc",
    )
    filters = body["query"]["bool"]["filter"]
    assert {"term": {"category_slug": "electronics"}} in filters
    assert {"term": {"in_stock": True}} in filters
    assert body["sort"] == [{"price": "asc"}]


def test_active_filter_always_applied() -> None:
    body = build_search_body("headphones")
    assert {"term": {"is_active": True}} in body["query"]["bool"]["filter"]
