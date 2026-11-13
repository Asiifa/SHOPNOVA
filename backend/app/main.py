import asyncio
import logging
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routers import addresses, admin, auth, cart, categories, inventory, orders, products, search
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.dev import ensure_dev_database
from app.database.session import get_engine
from app.kafka.producer import build_producer_config
from app.opensearch.index import ensure_product_index

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings.app_debug)
    ensure_dev_database()
    if settings.opensearch_configured():
        try:
            ensure_product_index()
            logger.info("OpenSearch index ensured: %s", settings.opensearch_index)
        except Exception:
            logger.exception("OpenSearch index creation skipped; search returns 502 until OpenSearch is reachable")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
    app = FastAPI(
        title="SHOPNOVA API",
        version="1.0.0",
        description="Indian retail e-commerce API backed by Aiven PostgreSQL, Kafka and OpenSearch.",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    @app.exception_handler(Exception)
    async def unhandled(_request: Request, exc: Exception):  # type: ignore[unused-ignore]
        if settings.app_debug:
            return JSONResponse({"detail": "Internal error"}, status_code=500)
        return JSONResponse({"detail": "Internal error"}, status_code=500)

    app.include_router(auth.router)
    app.include_router(products.router)
    app.include_router(search.router)
    app.include_router(categories.router)
    app.include_router(cart.router)
    app.include_router(orders.router)
    app.include_router(addresses.router)
    app.include_router(inventory.router)
    app.include_router(admin.router)

    @app.get("/api/health")
    async def health() -> dict:
        s = get_settings()

        pg_engine = get_engine() if s.postgres_configured() else None
        pg_reachable = False
        pg_detail = "not_configured"
        if pg_engine is not None:
            try:
                with pg_engine.connect() as conn:
                    conn.exec_driver_sql("SELECT 1")
                pg_reachable = True
                pg_detail = "reachable"
            except Exception as exc:
                pg_detail = "unreachable"
                logger.warning("PostgreSQL health check failed", exc_info=settings.app_debug)

        kafka_configured = s.kafka_configured()
        kafka_reachable = None
        kafka_detail = "not_configured"
        if kafka_configured:
            try:

                async def _probe() -> str:
                    probe = AIOKafkaProducer(
                        **{
                            **build_producer_config(s),
                            "request_timeout_ms": 5000,
                        }
                    )
                    await probe.start()
                    try:
                        await probe.client.cluster.request_update()
                        return "reachable"
                    finally:
                        await probe.stop()

                kafka_detail = asyncio.run(_probe())
                kafka_reachable = True
            except Exception as exc:
                kafka_reachable = False
                kafka_detail = "unreachable"
                logger.warning("Kafka health check failed", exc_info=settings.app_debug)

        os_configured = s.opensearch_configured()
        os_reachable = False
        os_detail = "not_configured"
        if os_configured:
            try:
                from app.opensearch.client import get_opensearch_client

                client = get_opensearch_client()
                client.info()
                os_reachable = True
                os_detail = "reachable"
            except Exception as exc:
                os_detail = "unreachable"
                logger.warning("OpenSearch health check failed", exc_info=settings.app_debug)

        configured = pg_engine is not None and kafka_configured and os_configured
        reachable = pg_reachable and (kafka_reachable is not False) and os_reachable
        return {
            "status": "ok" if (configured and reachable) else "degraded",
            "service": s.app_name,
            "postgres_configured": pg_engine is not None,
            "postgres_reachable": pg_reachable,
            "postgres_detail": pg_detail,
            "kafka_configured": kafka_configured,
            "kafka_reachable": kafka_reachable,
            "kafka_detail": kafka_detail,
            "opensearch_configured": os_configured,
            "opensearch_reachable": os_reachable,
            "opensearch_detail": os_detail,
            "ready": configured and pg_reachable,
        }

    @app.get("/")
    def root() -> dict:
        return {"name": "SHOPNOVA", "docs": "/api/docs"}

    return app


app = create_app()
