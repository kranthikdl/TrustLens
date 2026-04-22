"""Unit tests for the HTTP-boundary schemas in :mod:`api.schemas`."""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from api import schemas
from api.models import Badge, ContentItem, TrustScore, TrustSignal
from api.schemas import (
    ErrorResponse,
    TrustCalculateRequest,
    TrustCalculateResponse,
)


def _content() -> ContentItem:
    return ContentItem(
        url="https://example.com/article",
        title="Example",
        body="Hello world",
    )


def _score() -> TrustScore:
    return TrustScore(
        overall=87.5,
        signals=[TrustSignal(name="domain_age", weight=0.3, value=0.85)],
        computed_at=datetime(2026, 4, 22, 12, 0, 0, tzinfo=timezone.utc),
    )


def _badge() -> Badge:
    return Badge(level="high", color="#2ecc71", label="High Trust")


class TestTrustCalculateRequest:
    def test_accepts_valid_content_item(self):
        req = TrustCalculateRequest(content=_content())
        assert str(req.content.url).startswith("https://example.com/")
        assert req.content.title == "Example"
        assert req.content.body == "Hello world"

    def test_accepts_dict_coerced_to_content_item(self):
        req = TrustCalculateRequest(
            content={
                "url": "https://example.com/a",
                "title": "t",
                "body": "b",
            }
        )
        assert isinstance(req.content, ContentItem)

    def test_rejects_missing_content(self):
        with pytest.raises(ValidationError):
            TrustCalculateRequest()  # type: ignore[call-arg]

    @pytest.mark.parametrize("field", ["url", "title", "body"])
    def test_rejects_content_missing_required_field(self, field):
        payload = {
            "url": "https://example.com/a",
            "title": "t",
            "body": "b",
        }
        payload.pop(field)
        with pytest.raises(ValidationError):
            TrustCalculateRequest(content=payload)

    def test_rejects_invalid_url_in_content(self):
        with pytest.raises(ValidationError):
            TrustCalculateRequest(
                content={"url": "not-a-url", "title": "t", "body": "b"}
            )


class TestTrustCalculateResponse:
    def test_top_level_keys_are_score_and_badge(self):
        resp = TrustCalculateResponse(score=_score(), badge=_badge())
        dumped = resp.model_dump()
        assert set(dumped.keys()) == {"score", "badge"}

    def test_json_serialization_contains_score_and_badge(self):
        resp = TrustCalculateResponse(score=_score(), badge=_badge())
        parsed = json.loads(resp.model_dump_json())
        assert "score" in parsed
        assert "badge" in parsed
        assert parsed["score"]["overall"] == 87.5
        assert parsed["badge"]["level"] == "high"

    def test_rejects_missing_score(self):
        with pytest.raises(ValidationError):
            TrustCalculateResponse(badge=_badge())  # type: ignore[call-arg]

    def test_rejects_missing_badge(self):
        with pytest.raises(ValidationError):
            TrustCalculateResponse(score=_score())  # type: ignore[call-arg]


class TestErrorResponse:
    def test_error_required_detail_optional(self):
        err = ErrorResponse(error="validation_error")
        assert err.error == "validation_error"
        assert err.detail is None

    def test_accepts_detail(self):
        err = ErrorResponse(error="validation_error", detail="url invalid")
        assert err.detail == "url invalid"

    def test_rejects_missing_error(self):
        with pytest.raises(ValidationError):
            ErrorResponse()  # type: ignore[call-arg]


class TestJsonSchemaExamples:
    """Each schema's json_schema_extra example must validate against itself."""

    @pytest.mark.parametrize(
        "model",
        [TrustCalculateRequest, TrustCalculateResponse, ErrorResponse],
    )
    def test_example_present_in_model_config(self, model):
        example = model.model_config.get("json_schema_extra", {}).get("example")
        assert example is not None, f"{model.__name__} is missing a json_schema_extra example"

    def test_request_example_validates(self):
        example = TrustCalculateRequest.model_config["json_schema_extra"]["example"]
        TrustCalculateRequest.model_validate(example)

    def test_response_example_validates(self):
        example = TrustCalculateResponse.model_config["json_schema_extra"]["example"]
        TrustCalculateResponse.model_validate(example)

    def test_error_example_validates(self):
        example = ErrorResponse.model_config["json_schema_extra"]["example"]
        ErrorResponse.model_validate(example)


def test_top_level_imports_succeed():
    """Acceptance-criteria smoke test."""
    from api.schemas import (  # noqa: F401
        ErrorResponse,
        TrustCalculateRequest,
        TrustCalculateResponse,
    )


def test_schemas_reexports_domain_models():
    """Route code should only need to import from api.schemas."""
    assert schemas.ContentItem is ContentItem
    assert schemas.TrustScore is TrustScore
    assert schemas.Badge is Badge
    assert schemas.TrustSignal is TrustSignal
