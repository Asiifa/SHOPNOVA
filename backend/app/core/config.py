"""Secure configuration loader. Never logs secret values."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "SHOPNOVA"
    app_env: str = "development"
    app_debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = Field(default="dev-only-change-me", min_length=16)
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:5173"
    frontend_origin: str = "http://localhost:5173"
    rate_limit_login: str = "5/minute"
    rate_limit_default: str = "60/minute"

    postgres_host: str = ""
    postgres_port: int = 21584
    postgres_db: str = "defaultdb"
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_sslmode: str = "verify-full"
    aiven_ca_path: str = "./certs/aiven-ca.pem"

    kafka_bootstrap_servers: str = ""
    kafka_security_protocol: str = "SASL_SSL"
    kafka_sasl_mechanism: str = "SCRAM-SHA-256"
    kafka_sasl_username: str = ""
    kafka_sasl_password: str = ""
    kafka_ssl_cafile: str = "./certs/aiven-ca.pem"
    kafka_client_id: str = "shopnova-api"
    kafka_topic_prefix: str = "shopnova."
    kafka_auto_create_topics: bool = False

    opensearch_url: str = ""
    opensearch_user: str = ""
    opensearch_password: str = ""
    opensearch_verify_certs: bool = True
    opensearch_ca_certs: str = "./certs/aiven-ca.pem"
    opensearch_index: str = "shopnova-products"

    aiven_pg_service: str = "pg-39f21b1d"
    aiven_kafka_service: str = "kafka-12572b23"
    aiven_os_service: str = "os-114c34a2"

    outbox_poll_interval_seconds: float = 2.0
    consumer_poll_timeout_ms: int = 1000
    seed_demo_data: bool = False
    admin_bootstrap_email: str = ""
    admin_bootstrap_password: str = ""

    @field_validator("cors_origins")
    @classmethod
    def _strip_origins(cls, value: str) -> str:
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def resolve_path(self, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute():
            return path
        return (BACKEND_ROOT / path).resolve()

    @property
    def ca_path(self) -> Path:
        return self.resolve_path(self.aiven_ca_path)

    def database_url(self) -> str:
        # Password is interpolated by the driver via connect_args, not logged.
        from urllib.parse import quote_plus

        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def kafka_topics(self) -> dict[str, str]:
        prefix = self.kafka_topic_prefix
        return {
            "order": f"{prefix}order-events",
            "inventory": f"{prefix}inventory-events",
            "product": f"{prefix}product-events",
            "notification": f"{prefix}notification-events",
            "dlq": f"{prefix}dead-letter-events",
        }

    def postgres_configured(self) -> bool:
        return bool(self.postgres_host and self.postgres_user and self.postgres_password)

    def kafka_configured(self) -> bool:
        return bool(
            self.kafka_bootstrap_servers
            and self.kafka_sasl_username
            and self.kafka_sasl_password
        )

    def opensearch_configured(self) -> bool:
        return bool(self.opensearch_url and self.opensearch_user and self.opensearch_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()
