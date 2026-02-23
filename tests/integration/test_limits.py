from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.middleware import RateLimiter
from app.main import app


def _set_settings(settings: Settings) -> None:
    app.state.settings = settings
    app.state.rate_limiter = RateLimiter(
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


def test_rate_limit_enforced():
    original_settings = app.state.settings
    original_limiter = app.state.rate_limiter
    try:
        _set_settings(
            Settings(
                rate_limit_enabled=True,
                rate_limit_max_requests=2,
                rate_limit_window_seconds=60,
                max_body_size_bytes=1_000_000,
            )
        )
        client = TestClient(app)
        payload = {"task": {"name": "X"}, "activity": []}
        assert client.post("/summarize", json=payload).status_code == 200
        assert client.post("/summarize", json=payload).status_code == 200
        r = client.post("/summarize", json=payload)
        assert r.status_code == 429
    finally:
        app.state.settings = original_settings
        app.state.rate_limiter = original_limiter


def test_body_size_limit_enforced():
    original_settings = app.state.settings
    original_limiter = app.state.rate_limiter
    try:
        _set_settings(
            Settings(
                rate_limit_enabled=False,
                rate_limit_max_requests=60,
                rate_limit_window_seconds=60,
                max_body_size_bytes=200,
            )
        )
        client = TestClient(app)
        payload = {
            "task": {"name": "X", "description": "a" * 500},
            "activity": [],
        }
        r = client.post("/summarize", json=payload)
        assert r.status_code == 413
    finally:
        app.state.settings = original_settings
        app.state.rate_limiter = original_limiter
