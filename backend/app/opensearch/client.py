from __future__ import annotations

import logging
from functools import lru_cache

from opensearchpy import OpenSearch

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_opensearch_client() -> OpenSearch:
    settings = get_settings()
    if not settings.opensearch_configured():
        raise RuntimeError("OpenSearch is not configured. Fill OPENSEARCH_* in backend/.env privately.")
    verify = settings.opensearch_verify_certs
    return OpenSearch(
        hosts=[settings.opensearch_url],
        http_auth=(settings.opensearch_user, settings.opensearch_password),
        use_ssl=settings.opensearch_url.startswith("https"),
        verify_certs=verify,
        ssl_show_warn=verify,
        timeout=20,
        max_retries=2,
        retry_on_timeout=True,
    )
