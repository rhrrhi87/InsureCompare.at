"""Token-bucket rate limit middleware (per client IP).

File: backend/app/core/rate_limit.py

In a production multi-instance deployment, replace the in-process counter
with Redis (e.g. ``slowapi`` backed by aioredis). The interface below is
deliberately compatible.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Reject more than ``requests_per_minute`` calls per client IP."""

    def __init__(self, app, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.limit = requests_per_minute
        self.window_seconds = 60
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = self._buckets[client_ip]

        # Drop timestamps that fall outside the window
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after_seconds": int(self.window_seconds - (now - bucket[0])),
                },
            )

        bucket.append(now)
        return await call_next(request)
