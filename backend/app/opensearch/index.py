from __future__ import annotations

import logging

from app.core.config import get_settings
from app.opensearch.client import get_opensearch_client

logger = logging.getLogger(__name__)

INDEX_BODY = {
    "settings": {
        "index": {"number_of_shards": 1, "number_of_replicas": 0},
        "analysis": {
            "filter": {
                "autocomplete_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 15,
                }
            },
            "analyzer": {
                "autocomplete": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "autocomplete_filter"],
                },
                "autocomplete_search": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase"],
                },
            },
        },
    },
    "mappings": {
        "properties": {
            "product_id": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "autocomplete": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"},
                    "keyword": {"type": "keyword", "ignore_above": 256},
                },
            },
            "description": {"type": "text"},
            "brand": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "category": {"type": "keyword"},
            "category_slug": {"type": "keyword"},
            "price": {"type": "double"},
            "city": {"type": "keyword"},
            "specifications": {"type": "text"},
            "available_quantity": {"type": "integer"},
            "in_stock": {"type": "boolean"},
            "is_active": {"type": "boolean"},
            "rating": {"type": "double"},
            "sold_count": {"type": "integer"},
            "image_url": {"type": "keyword", "index": False},
            "updated_at": {"type": "date"},
            "version": {"type": "long"},
        }
    },
}


def ensure_product_index() -> str:
    settings = get_settings()
    client = get_opensearch_client()
    name = settings.opensearch_index
    if not client.indices.exists(index=name):
        client.indices.create(index=name, body=INDEX_BODY)
        logger.info("Created OpenSearch index %s", name)
    return name
