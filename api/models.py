"""Canonical Pydantic v2 domain models for TrustLens.

This module defines the pure data types used across the API and the
Chrome extension contract. It intentionally has no FastAPI or DB
dependencies so it can be unit-tested in isolation. HTTP-boundary
schemas live in ``api/schemas.py`` and wrap these types.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TrustSignal(BaseModel):
    """A single trust signal contributing to an overall trust score.

    Example:
        >>> TrustSignal(name="domain_age", weight=0.3, value=0.85)
        TrustSignal(name='domain_age', weight=0.3, value=0.85)
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Identifier of the signal, e.g. 'domain_age'.")
    weight: float = Field(..., description="Relative contribution of the signal.")
    value: float = Field(..., description="Raw signal value supplied by the validator.")


class ContentItem(BaseModel):
    """A piece of web content under evaluation.

    Example:
        >>> ContentItem(
        ...     url="https://example.com/article",
        ...     title="Example",
        ...     body="Hello world",
        ... )  # doctest: +ELLIPSIS
        ContentItem(url=..., title='Example', body='Hello world')
    """

    model_config = ConfigDict(frozen=True)

    url: HttpUrl = Field(..., description="Canonical URL of the content.")
    title: str = Field(..., description="Page or article title.")
    body: str = Field(..., description="Extracted text body of the content.")


class TrustScore(BaseModel):
    """Aggregate trust score for a ContentItem.

    ``overall`` is constrained to the inclusive 0-100 range; values
    outside this range raise ``pydantic.ValidationError``.

    Example:
        >>> TrustScore(
        ...     overall=87.5,
        ...     signals=[TrustSignal(name="domain_age", weight=0.3, value=0.85)],
        ...     computed_at=datetime(2026, 4, 22, 12, 0, 0, tzinfo=timezone.utc),
        ... )  # doctest: +ELLIPSIS
        TrustScore(overall=87.5, signals=[...], computed_at=...)
    """

    model_config = ConfigDict(frozen=True)

    overall: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall trust score in the inclusive range 0-100.",
    )
    signals: list[TrustSignal] = Field(
        ..., description="Per-signal breakdown contributing to the overall score."
    )
    computed_at: datetime = Field(
        ..., description="Timestamp the score was computed."
    )


class Badge(BaseModel):
    """Visual trust badge derived from a TrustScore.

    Example:
        >>> Badge(level="high", color="#2ecc71", label="High Trust")
        Badge(level='high', color='#2ecc71', label='High Trust')
    """

    model_config = ConfigDict(frozen=True)

    level: Literal["low", "medium", "high", "verified"] = Field(
        ..., description="Categorical trust tier displayed to the user."
    )
    color: str = Field(..., description="CSS color string used to render the badge.")
    label: str = Field(..., description="Human-readable badge label.")


__all__ = ["TrustSignal", "ContentItem", "TrustScore", "Badge"]
