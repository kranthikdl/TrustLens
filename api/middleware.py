"""Middleware registration for the TrustLens FastAPI app.

Exports:
    register_middleware(app): attaches CORS (permitting chrome-extension://*
    and localhost) plus a lightweight request-logging middleware.
"""
from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("trustlens.api")

# Match chrome-extension://<id>, http(s)://localhost[:port], and
# http(s)://127.0.0.1[:port]. Used as allow_origin_regex so the Chrome
# extension (Ticket 8) can call the API without a hardcoded extension id.
_ORIGIN_REGEX = (
    r"^(chrome-extension://.*"
    r"|https?://localhost(:\d+)?"
    r"|https?://127\.0\.0\.1(:\d+)?)$"
)

_EXPLICIT_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
]


def register_middleware(app: FastAPI) -> None:
    """Register CORS and request-logging middleware on the given app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_EXPLICIT_ORIGINS,
        allow_origin_regex=_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
