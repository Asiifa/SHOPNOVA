from app.opensearch.client import get_opensearch_client
from app.opensearch.index import ensure_product_index

__all__ = ["get_opensearch_client", "ensure_product_index"]
