"""Local development database bootstrap.

When Aiven PostgreSQL is not configured, SHOPNOVA falls back to a local SQLite
database so the catalogue, orders and admin screens work without credentials.
Production deployments configure PostgreSQL in backend/.env and never hit this path.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect

from app.database.base import Base
from app.database.session import get_engine, get_session_factory

logger = logging.getLogger(__name__)


def is_dev_database() -> bool:
    from app.core.config import get_settings

    return not get_settings().postgres_configured()


def ensure_dev_database() -> None:
    """Create the schema and seed demo data for the local SQLite fallback.

    Idempotent: creates missing tables and only seeds when the catalogue is empty.
    """
    if not is_dev_database():
        return

    import app.models  # noqa: F401  (register every table on Base.metadata)

    engine = get_engine()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    if "categories" not in inspector.get_table_names():
        logger.warning("Dev database schema missing; skipping catalogue seed")
        return

    factory = get_session_factory()
    if factory is None:
        return

    with factory() as session:
        from app.models.catalog import Category

        if session.query(Category).count() > 0:
            logger.info("Dev database already seeded; skipping")
            return

    from scripts.seed_catalog import seed_catalog

    seeded = seed_catalog(factory)
    logger.info("Seeded dev catalogue with %s products", seeded)