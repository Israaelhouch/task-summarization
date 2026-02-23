import time
import uuid

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from app.core.config import Settings
from app.core.logging import bind_request_id, reset_request_id, setup_logging
from app.core.middleware import RateLimiter, get_client_key
from app.api.routes.summarize import router as summarize_router


settings = Settings.from_env()
logger = setup_logging(settings.log_level, settings.log_format)

rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

app = FastAPI()
app.state.settings = settings
app.state.rate_limiter = rate_limiter
app.include_router(summarize_router)


@app.middleware("http")
async def body_size_limit_middleware(request: Request, call_next):
    current_settings = request.app.state.settings
    max_bytes = current_settings.max_body_size_bytes
    if max_bytes > 0:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request body too large"},
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header"},
                )

        body = await request.body()
        if len(body) > max_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )

    return await call_next(request)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    current_settings = request.app.state.settings
    if not current_settings.rate_limit_enabled:
        return await call_next(request)

    client_host = request.client.host if request.client else None
    key = get_client_key(request.headers, client_host)
    limiter = request.app.state.rate_limiter
    allowed, retry_after = await limiter.allow(key)
    if not allowed:
        headers = {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers=headers,
        )

    return await call_next(request)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = (
        request.headers.get("x-request-id")
        or request.headers.get("x-correlation-id")
        or str(uuid.uuid4())
    )
    token = bind_request_id(request_id)
    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        client_host = request.client.host if request.client else None
        client_ip = get_client_key(request.headers, client_host)
        logger.exception(
            "request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent"),
                "content_length": request.headers.get("content-length"),
            },
        )
        reset_request_id(token)
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-Id"] = request_id
    client_host = request.client.host if request.client else None
    client_ip = get_client_key(request.headers, client_host)
    logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "content_length": request.headers.get("content-length"),
        },
    )
    reset_request_id(token)
    return response


@app.get("/")
def health():
    return {"status": "ok"}
