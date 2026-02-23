from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict, Tuple

import asyncio


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max(1, max_requests)
        self._window_seconds = max(1, window_seconds)
        self._hits: Dict[str, Deque[float]] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> Tuple[bool, int | None]:
        now = time.monotonic()
        async with self._lock:
            bucket = self._hits.get(key)
            if bucket is None:
                bucket = deque()
                self._hits[key] = bucket

            cutoff = now - self._window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= self._max_requests:
                retry_after = int(self._window_seconds - (now - bucket[0])) if bucket else self._window_seconds
                if retry_after < 1:
                    retry_after = 1
                return False, retry_after

            bucket.append(now)
            return True, None


def get_client_key(headers: Dict[str, str], client_host: str | None) -> str:
    forwarded_for = headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return client_host or "unknown"
