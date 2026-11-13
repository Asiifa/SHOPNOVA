from collections.abc import AsyncGenerator, Generator

from fastapi import HTTPException, status
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import BACKEND_ROOT, get_settings

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _build_sqlite_engine():
    """Local development fallback so the API and catalogue work without Aiven.

    Only used when PostgreSQL is not configured. A file-backed SQLite database
    keeps the same SQLAlchemy models/routers, so products are still served from a
    real database rather than hardcoded in the frontend.
    """
    db_path = BACKEND_ROOT / "dev.db"
    return create_engine(
        f"sqlite:///{db_path.as_posix()}",
        future=True,
        connect_args={"check_same_thread": False, "timeout": 30},
    )


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        if not settings.postgres_configured():
            _engine = _build_sqlite_engine()
        else:
            connect_args: dict = {"sslmode": settings.postgres_sslmode}
            ca = settings.ca_path
            if settings.postgres_sslmode in {"verify-full", "verify-ca"}:
                if not ca.exists():
                    raise RuntimeError(
                        f"Aiven CA certificate not found at {ca}. Download it from the Aiven "
                        "console into backend/certs/aiven-ca.pem."
                    )
                connect_args["sslrootcert"] = str(ca)
            _engine = create_engine(
                settings.database_url(),
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                connect_args=connect_args,
            )

            @event.listens_for(_engine, "connect")
            def _set_utc(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
                cursor = dbapi_connection.cursor()
                cursor.execute("SET TIME ZONE 'UTC'")
                cursor.close()

        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session] | None:
    get_engine()
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    factory = get_session_factory()
    if factory is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "PostgreSQL is not configured. Copy backend/.env.example to backend/.env and fill Aiven connection values privately.",
        )
    session = factory()
    try:
        yield session
    finally:
        session.close()


async def get_db_async() -> AsyncGenerator[Session, None]:
    # Sync SQLAlchemy is used with FastAPI via threadpool for psycopg reliability
    # with Aiven TLS. Endpoints that need transactions use the sync Session.
    factory = get_session_factory()
    if factory is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "PostgreSQL is not configured.",
        )
    session = factory()
    try:
        yield session
    finally:
        session.close()
