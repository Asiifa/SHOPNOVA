"""These tests must not be marked passing unless Aiven credentials are configured and live checks run."""

import pytest

from app.core.config import get_settings

pytestmark = pytest.mark.integration


def test_credentials_are_required_for_live_checks() -> None:
    settings = get_settings()
    if not (settings.postgres_configured() and settings.kafka_configured() and settings.opensearch_configured()):
        pytest.skip("Aiven credentials are not configured in backend/.env")
    pytest.skip("Live Aiven tests run via: python -m scripts.verify_services after private configuration")
