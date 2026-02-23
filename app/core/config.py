from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _env_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    rate_limit_enabled: bool = True
    rate_limit_max_requests: int = 60
    rate_limit_window_seconds: int = 60
    max_body_size_bytes: int = 1_000_000
    log_level: str = "INFO"
    log_format: str = "json"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            rate_limit_enabled=_env_bool(os.getenv("RATE_LIMIT_ENABLED"), True),
            rate_limit_max_requests=_env_int(os.getenv("RATE_LIMIT_MAX_REQUESTS"), 60),
            rate_limit_window_seconds=_env_int(os.getenv("RATE_LIMIT_WINDOW_SECONDS"), 60),
            max_body_size_bytes=_env_int(os.getenv("MAX_BODY_SIZE_BYTES"), 1_000_000),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
        )
