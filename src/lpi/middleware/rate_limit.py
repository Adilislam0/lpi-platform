"""Rate limiting middleware — fixed-window per client IP.

Limits (per IP, per 60-second window):
  - /health liveness probe:               120 req/min
  - Write methods (POST/PATCH/PUT/DELETE): 30 req/min
  - Read methods (GET, etc.):              60 req/min

Returns HTTP 429 with a Retry-After header when the limit is exceeded.
OPTIONS requests (CORS preflight) are always exempt.

State is in-memory and single-process. For multi-worker deployments,
replace _store with a Redis-backed counter.
"""

import os, time
from collections.abc import Awaitable, Callable
from urllib import request

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_WINDOW_SECONDS = 60
_WRITE_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})

_HEALTH_LIMIT = 120
_WRITE_LIMIT = 30
_READ_LIMIT = 60

# (client_ip, "limit_type:window_bucket") -> request_count
_store: dict[tuple[str, str], int] = {}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check(ip: str, limit_type: str, limit: int) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds). Increments counter if allowed."""
    now = time.time()
    bucket = int(now // _WINDOW_SECONDS)
    key = (ip, f"{limit_type}:{bucket}")

    count = _store.get(key, 0)
    if count >= limit:
        return False, _WINDOW_SECONDS - int(now % _WINDOW_SECONDS)

    _store[key] = count + 1

    # Purge stale buckets to prevent unbounded memory growth.
    if len(_store) > 10_000:
        stale = bucket - 2
        for k in [k for k in _store if int(k[1].rsplit(":", 1)[-1]) <= stale]:
            del _store[k]

    return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window rate limiter keyed on client IP and request type."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # CORS preflight — never count against limits.
        if request.method == "OPTIONS":
            return await call_next(request)

        ip = _client_ip(request)
        path = request.url.path
        method = request.method

        if path == "/health":
            limit_type, limit = "health", _HEALTH_LIMIT
        elif method in _WRITE_METHODS:
            limit_type, limit = "write", _WRITE_LIMIT
        else:
            limit_type, limit = "read", _READ_LIMIT

        allowed, retry_after = _check(ip, limit_type, limit)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
