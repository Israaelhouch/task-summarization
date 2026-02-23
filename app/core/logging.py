from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional


_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def bind_request_id(request_id: str) -> Any:
    return _request_id_ctx.set(request_id)


def reset_request_id(token: Any) -> None:
    _request_id_ctx.reset(token)


def get_request_id() -> Optional[str]:
    return _request_id_ctx.get()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id

        for key in ("method", "path", "status_code", "duration_ms", "client_ip", "user_agent", "content_length"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def setup_logging(level: str = "INFO", log_format: str = "json") -> logging.Logger:
    logger = logging.getLogger("app")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )

    logger.setLevel(level.upper())
    logger.addHandler(handler)
    logger.propagate = False
    return logger
