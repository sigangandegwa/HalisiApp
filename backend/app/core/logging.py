"""Structured one-line logging. Never log secrets or full phone numbers (use ``payment.mask_phone``)."""

import json
import logging
import sys
from typing import Any

logger = logging.getLogger("halisi")


class _JsonFormatter(logging.Formatter):
    """``{"ts", "level", "logger", "msg", ...extra}`` per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        payload.update(getattr(record, "fields", {}) or {})
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure the ``halisi`` logger once (idempotent)."""
    if not any(getattr(h, "_halisi", False) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        handler._halisi = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level)
    return logger


def log_event(message: str, **fields: Any) -> None:
    """Log one structured event, e.g. ``log_event("check", scan_id=..., verdict=..., elapsed_ms=...)``."""
    logger.info(message, extra={"fields": fields})
