"""Unit tests for the canonical Pydantic v2 domain models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from api.models import Badge, ContentItem, TrustScore, TrustSignal


def _signal() -> TrustSignal:
    return TrustSignal(name="domain_age", weight=0.3, value=0.85)


def _now() -> datetime:
    return datetime(2026, 4, 22, 12, 0, 0, tzinfo=timezone.utc)


class TestTrustSignal:
    def test_instantiation_with_example_values(self):
        signal = TrustSignal(name="domain_age", weight=0.3, value=0.85)
        assert signal.name == "domain_age"
        assert signal.weight == 0.3
        assert signal.value == 0.85

    def test_is_frozen(self):
        signal = _signal()
        with pytest.raises(ValidationError):
            signal.name = "other"  # type: ignore[misc]


class TestContentItem:
    def test_instantiation_with_example_values(self):
        item = ContentItem(
            url="https://example.com/article",
            title="Example",
            body="Hello world",
        )
        assert str(item.url).startswith("https://example.com/")
        assert item.title == "Example"
        assert item.body == "Hello world"

    def test_invalid_url_rejected(self):
        with pytest.raises(ValidationError):
            ContentItem(url="not-a-url", title="t", body="b")


class TestTrustScore:
    def test_instantiation_with_example_values(self):
        score = TrustScore(
            overall=87.5,
            signals=[_signal()],
            computed_at=_now(),
        )
        assert score.overall == 87.5
        assert score.signals[0].name == "domain_age"
        assert score.computed_at == _now()

    def test_overall_accepts_lower_bound(self):
        score = TrustScore(overall=0, signals=[], computed_at=_now())
        assert score.overall == 0

    def test_overall_accepts_upper_bound(self):
        score = TrustScore(overall=100, signals=[], computed_at=_now())
        assert score.overall == 100

    def test_overall_rejects_below_zero(self):
        with pytest.raises(ValidationError):
            TrustScore(overall=-0.1, signals=[], computed_at=_now())

    def test_overall_rejects_above_one_hundred(self):
        with pytest.raises(ValidationError):
            TrustScore(overall=100.1, signals=[], computed_at=_now())


class TestBadge:
    @pytest.mark.parametrize("level", ["low", "medium", "high", "verified"])
    def test_accepts_allowed_levels(self, level):
        badge = Badge(level=level, color="#fff", label="x")
        assert badge.level == level

    def test_instantiation_with_example_values(self):
        badge = Badge(level="high", color="#2ecc71", label="High Trust")
        assert badge.level == "high"
        assert badge.color == "#2ecc71"
        assert badge.label == "High Trust"

    @pytest.mark.parametrize("level", ["unknown", "LOW", "trusted", ""])
    def test_rejects_other_levels(self, level):
        with pytest.raises(ValidationError):
            Badge(level=level, color="#fff", label="x")


def test_top_level_imports_succeed():
    """Mirrors the acceptance-criteria smoke test."""
    from api.models import Badge, ContentItem, TrustScore, TrustSignal  # noqa: F401
