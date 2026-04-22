"""HTTP request/response schemas for the TrustLens API.

These Pydantic v2 models define the wire format for the trust endpoint
and wrap the canonical domain models from :mod:`api.models`. Route code
should import only from this module so that the HTTP boundary stays
stable as internal models evolve.
"""

from pydantic import BaseModel, ConfigDict, Field

from api.models import Badge, ContentItem, TrustScore, TrustSignal

_REQUEST_EXAMPLE = {
    "content": {
        "url": "https://example.com/article",
        "title": "Example Article",
        "body": "Hello world, this is an article body.",
    }
}

_RESPONSE_EXAMPLE = {
    "score": {
        "overall": 87.5,
        "signals": [{"name": "domain_age", "weight": 0.3, "value": 0.85}],
        "computed_at": "2026-04-22T12:00:00Z",
    },
    "badge": {"level": "high", "color": "#2ecc71", "label": "High Trust"},
}

_ERROR_EXAMPLE = {"error": "validation_error", "detail": "url is not a valid URL"}


class TrustCalculateRequest(BaseModel):
    """Request body for ``POST /trust/calculate``."""

    model_config = ConfigDict(json_schema_extra={"example": _REQUEST_EXAMPLE})

    content: ContentItem = Field(..., description="Web content to evaluate.")


class TrustCalculateResponse(BaseModel):
    """Response body for ``POST /trust/calculate``."""

    model_config = ConfigDict(json_schema_extra={"example": _RESPONSE_EXAMPLE})

    score: TrustScore = Field(..., description="Computed trust score.")
    badge: Badge = Field(..., description="Visual badge derived from the score.")


class ErrorResponse(BaseModel):
    """Uniform error envelope returned by failing endpoints."""

    model_config = ConfigDict(json_schema_extra={"example": _ERROR_EXAMPLE})

    error: str = Field(..., description="Short machine-readable error code.")
    detail: str | None = Field(
        default=None, description="Optional human-readable explanation."
    )


__all__ = [
    "TrustCalculateRequest",
    "TrustCalculateResponse",
    "ErrorResponse",
    "ContentItem",
    "TrustScore",
    "Badge",
    "TrustSignal",
]
