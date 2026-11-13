"""Structured logging with secret redaction."""

import logging
import re
import sys

SECRET_PATTERNS = (
    re.compile(r"(password=)([^&\s]+)", re.I),
    re.compile(r"(passwd=)([^&\s]+)", re.I),
    re.compile(r"(secret=)([^&\s]+)", re.I),
    re.compile(r"(authorization:\s*bearer\s+)(\S+)", re.I),
    re.compile(r"(postgresql\+psycopg://[^:]+:)([^@]+)(@)", re.I),
)


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for pattern in SECRET_PATTERNS:
            message = pattern.sub(lambda m: m.group(1) + "***" + (m.group(3) if m.lastindex == 3 else ""), message)
        return message


def configure_logging(debug: bool = False) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        RedactingFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    logging.getLogger("aiokafka").setLevel(logging.WARNING)
    logging.getLogger("opensearch").setLevel(logging.WARNING)
