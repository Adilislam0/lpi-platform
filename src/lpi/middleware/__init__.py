"""LPI middleware package — Phase 2 scaffold.

Exposes:
    get_current_user   — returns "default_user" (Phase 2 stub)
    register_middleware — wires CORS + timing onto the FastAPI app

Phase 3: get_current_user will decode a real JWT Bearer token.
         Only auth.py changes — no router file needs to be touched.
"""

import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from lpi.middleware.auth import get_current_user  # re-exported for convenience

__all__ = ["get_current_user", "register_middleware"]


class TimingMiddleware(BaseHTTPMiddleware):
    """Adds X-Process-Time and X-Request-ID to every response.

    X-Process-Time lets the team verify the <3s recommendation target.
    X-Request-ID lets log entries across services be correlated.
    Neither header blocks or rejects any request.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        rid = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
        response.headers["X-Request-ID"] = rid
        return response


def register_middleware(app: FastAPI) -> None:
    """Attach all middleware to the app. Call once in main.py before routers."""
    app.add_middleware(TimingMiddleware)          # inner: measures route time only
    app.add_middleware(                           # outer: handles CORS pre-flight
        CORSMiddleware,
        allow_origins=["*"],                      # Phase 3: restrict to frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )