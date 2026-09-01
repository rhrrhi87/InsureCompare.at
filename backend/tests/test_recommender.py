"""Unit tests for the recommendation scoring engine.

File: backend/tests/test_recommender.py
"""
from __future__ import annotations

import pytest

from app.db.enums import (
    CoverageLevel,
    DeductiblePreference,
    ProductLine,
    RiskLevel,
    RiskTolerance,
)
from app.db.models import Policy, RiskProfile
from app.recommender import (
    DEFAULT_WEIGHTS,
    Recommender,
    find_counterfactual,
    normalise_weights,
)


@pytest.fixture
def profile() -> RiskProfile:
    return RiskProfile(
        id=1, user_id=1,
        insurance_type=ProductLine.CAR,
        monthly_budget_eur=100.0,
        risk_tolerance=RiskTolerance.MEDIUM,
        coverage_level=CoverageLevel.STANDARD,
        deductible_preference=DeductiblePreference.MEDIUM,
        household_size=1,
        property_value_eur=None,
        required_coverages=[],
        weights={},
    )


def _make_policy(**kwargs) -> Policy:
    defaults = {
        "id": 1,
        "provider_id": 1,
        "name": "Test Policy",
        "product_line": ProductLine.CAR,
        "monthly_premium_eur": 70.0,
        "annual_premium_eur": 840.0,
        "deductible_eur": 500.0,
        "coverage_limit_eur": 10_000_000.0,
        "risk_level": RiskLevel.LOW,
        "coverage_items": ["Liability coverage", "Comprehensive coverage"],
        "additional_features": [],
        "exclusions": [],
        "is_active": True,
    }
    defaults.update(kwargs)
    return Policy(**defaults)


def test_default_weights_sum_to_one() -> None:
    assert sum(DEFAULT_WEIGHTS.values()) == pytest.approx(1.0)


def test_normalise_weights_handles_partial_input() -> None:
    weights = normalise_weights({"price": 0.5, "coverage": 0.5})
    assert sum(weights.values()) == pytest.approx(1.0)
    # All five default keys are present
    assert set(weights) == set(DEFAULT_WEIGHTS)


def test_normalise_weights_handles_empty_input() -> None:
    weights = normalise_weights(None)
    assert weights == DEFAULT_WEIGHTS


def test_score_orders_descending(profile: RiskProfile) -> None:
    cheaper = _make_policy(id=1, monthly_premium_eur=50.0)
    pricier = _make_policy(id=2, monthly_premium_eur=120.0)
    scored = Recommender().score([pricier, cheaper], profile)
    assert scored[0].score >= scored[-1].score
    assert scored[0].policy.id == cheaper.id


def test_score_in_zero_to_hundred(profile: RiskProfile) -> None:
    policy = _make_policy()
    scored = Recommender().score([policy], profile)
    assert 0.0 <= scored[0].score <= 100.0


def test_breakdown_keys_match_features(profile: RiskProfile) -> None:
    policy = _make_policy()
    scored = Recommender().score([policy], profile)
    assert set(scored[0].breakdown) == {
        "price", "coverage", "exclusion", "deductible", "fit"
    }


def test_empty_candidate_list_returns_empty(profile: RiskProfile) -> None:
    assert Recommender().score([], profile) == []


def test_counterfactual_finds_smallest_deterministic_weight_change(
    profile: RiskProfile,
) -> None:
    broad = _make_policy(
        id=1,
        name="Broad Cover",
        monthly_premium_eur=100.0,
        coverage_items=["A", "B", "C", "D", "E"],
    )
    cheap = _make_policy(
        id=2,
        name="Budget Cover",
        monthly_premium_eur=20.0,
        coverage_items=["A", "B"],
    )
    scored = Recommender().score([broad, cheap], profile)
    assert scored[0].policy.id == broad.id

    explanation = find_counterfactual(scored, DEFAULT_WEIGHTS)

    assert explanation is not None
    assert explanation.current_policy_id == broad.id
    assert explanation.alternative_policy_id == cheap.id
    assert explanation.changed_feature in DEFAULT_WEIGHTS
    assert explanation.direction == (
        "increase"
        if explanation.suggested_weight > explanation.current_weight
        else "decrease"
    )
    assert sum(explanation.adjusted_weights.values()) == pytest.approx(1.0)

    rescored = Recommender(explanation.adjusted_weights).score(
        [broad, cheap], profile
    )
    assert rescored[0].policy.id == cheap.id


def test_counterfactual_is_none_for_single_candidate(
    profile: RiskProfile,
) -> None:
    scored = Recommender().score([_make_policy()], profile)
    assert find_counterfactual(scored, DEFAULT_WEIGHTS) is None
