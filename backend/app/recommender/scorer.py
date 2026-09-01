"""Weighted-additive recommendation scoring with SHAP-style explanations.

File: backend/app/recommender/scorer.py

The ranking function S(p, u) is a weighted sum of five normalised features
(price, coverage, exclusion penalty, deductible match, profile fit). Because
S is additive in feature contributions, the per-feature contribution is the
exact Shapley value of an additive linear model (symmetry + dummy axioms).
That property is what lets the SHAP-style explanation panel use the same
``contribution`` numbers without any TreeSHAP machinery.

Default weights match the production UI:
    Price 25 % · Coverage 30 % · Exclusion 20 % · Deductible 10 % · Match 15 %
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from app.db.enums import (
    CoverageLevel,
    DeductiblePreference,
    RiskLevel,
    RiskTolerance,
)
from app.db.models import Policy, RiskProfile

# ---------------------------------------------------------------------------
# Default weights (must sum to 1.0)
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS: dict[str, float] = {
    "price": 0.25,
    "coverage": 0.30,
    "exclusion": 0.20,
    "deductible": 0.10,
    "fit": 0.15,
}

FEATURE_LABELS: dict[str, str] = {
    "price": "Price",
    "coverage": "Coverage",
    "exclusion": "Exclusions",
    "deductible": "Deductible",
    "fit": "Preference Match",
}


def normalise_weights(weights: dict[str, float] | None) -> dict[str, float]:
    """Validate and normalise a weight dict to sum to 1.

    Missing keys are filled from ``DEFAULT_WEIGHTS``; the final values are
    rescaled so that ``sum(...) == 1`` to two decimals of precision.
    """
    if not weights:
        return dict(DEFAULT_WEIGHTS)

    merged = {**DEFAULT_WEIGHTS, **weights}
    total = sum(merged.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: v / total for k, v in merged.items()}


# ---------------------------------------------------------------------------
# Feature functions (each returns a value in [0, 1])
# ---------------------------------------------------------------------------
def _f_price(policy: Policy, profile: RiskProfile) -> float:
    """Higher = cheaper relative to user's monthly budget."""
    monthly = float(policy.monthly_premium_eur)
    budget = max(1.0, float(profile.monthly_budget_eur))
    if monthly <= budget:
        # Within budget; scale linearly so half-the-budget = 1.0.
        return float(np.clip(1.0 - 0.5 * (monthly / budget), 0.0, 1.0))
    # Over budget — penalise quadratically.
    overshoot = monthly / budget - 1.0
    return float(np.clip(0.5 - overshoot, 0.0, 1.0))


_COVERAGE_LEVEL_TARGET: dict[CoverageLevel, int] = {
    CoverageLevel.BASIC: 3,
    CoverageLevel.STANDARD: 5,
    CoverageLevel.COMPREHENSIVE: 8,
}


def _f_coverage(policy: Policy, profile: RiskProfile) -> float:
    """Coverage breadth vs the user's preferred level + required-coverage overlap."""
    target = _COVERAGE_LEVEL_TARGET[profile.coverage_level]
    breadth = min(len(policy.coverage_items) / target, 1.0)

    if profile.required_coverages:
        wanted = {c.lower() for c in profile.required_coverages}
        present = {c.lower() for c in policy.coverage_items}
        overlap = len(wanted & present) / max(len(wanted), 1)
        return float(0.5 * breadth + 0.5 * overlap)
    return float(breadth)


def _f_exclusion(policy: Policy, profile: RiskProfile) -> float:
    """Higher = fewer exclusions overlap with the user's required coverages."""
    if not policy.exclusions:
        return 1.0

    if profile.required_coverages:
        excl_lower = {e.lower() for e in policy.exclusions}
        wanted = {c.lower() for c in profile.required_coverages}
        overlap = len({c for c in wanted if any(c in e for e in excl_lower)})
        penalty = overlap / max(len(wanted), 1)
        return float(np.clip(1.0 - penalty, 0.0, 1.0))

    # No specific requirements; mild penalty per exclusion (capped).
    return float(np.clip(1.0 - 0.05 * len(policy.exclusions), 0.0, 1.0))


_DEDUCTIBLE_BUCKETS: dict[DeductiblePreference, tuple[float, float]] = {
    DeductiblePreference.LOW: (150.0, 300.0),
    DeductiblePreference.MEDIUM: (400.0, 600.0),
    DeductiblePreference.HIGH: (700.0, 1000.0),
}


def _f_deductible(policy: Policy, profile: RiskProfile) -> float:
    """1.0 if the policy deductible falls inside the user's preferred bucket."""
    low, high = _DEDUCTIBLE_BUCKETS[profile.deductible_preference]
    deductible = float(policy.deductible_eur)
    if low <= deductible <= high:
        return 1.0
    # Distance-based fall-off
    diff = low - deductible if deductible < low else deductible - high
    return float(np.clip(1.0 - diff / 1000.0, 0.0, 1.0))


_RISK_TOLERANCE_VS_LEVEL: dict[
    tuple[RiskTolerance, RiskLevel], float
] = {
    (RiskTolerance.LOW, RiskLevel.LOW): 1.00,
    (RiskTolerance.LOW, RiskLevel.MEDIUM): 0.65,
    (RiskTolerance.LOW, RiskLevel.HIGH): 0.30,
    (RiskTolerance.MEDIUM, RiskLevel.LOW): 0.85,
    (RiskTolerance.MEDIUM, RiskLevel.MEDIUM): 1.00,
    (RiskTolerance.MEDIUM, RiskLevel.HIGH): 0.70,
    (RiskTolerance.HIGH, RiskLevel.LOW): 0.70,
    (RiskTolerance.HIGH, RiskLevel.MEDIUM): 0.90,
    (RiskTolerance.HIGH, RiskLevel.HIGH): 1.00,
}


def _f_fit(policy: Policy, profile: RiskProfile) -> float:
    """Profile-level fit (risk tolerance vs policy risk level + product line match)."""
    line_match = 1.0 if policy.product_line == profile.insurance_type else 0.0
    risk_match = _RISK_TOLERANCE_VS_LEVEL.get(
        (profile.risk_tolerance, policy.risk_level), 0.6
    )
    return float(0.5 * line_match + 0.5 * risk_match)


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------
@dataclass
class FeatureContributionDC:
    feature: str
    weight: float
    value: float
    contribution: float
    direction: str
    label: str


@dataclass
class ScoredPolicyDC:
    policy: Policy
    score: float
    breakdown: dict[str, float]
    contributions: list[FeatureContributionDC]
    narrative: str


@dataclass
class CounterfactualExplanationDC:
    """Smallest tested one-factor preference change that changes the winner.

    The changed feature is searched on a one-percentage-point grid from 5%
    to 80%. All other weights retain their relative proportions and are
    rescaled to keep the total at 100%. No LLM participates in this result.
    """

    current_policy_id: int
    current_policy_name: str
    alternative_policy_id: int
    alternative_policy_name: str
    changed_feature: str
    direction: str
    current_weight: float
    suggested_weight: float
    adjusted_weights: dict[str, float]
    current_policy_score: float
    alternative_policy_score: float
    score_margin: float


class Recommender:
    """Compute scores for a candidate set of policies given a profile."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = normalise_weights(weights)

    def score(
        self,
        candidates: Sequence[Policy],
        profile: RiskProfile,
    ) -> list[ScoredPolicyDC]:
        if not candidates:
            return []

        scored: list[ScoredPolicyDC] = []
        for policy in candidates:
            f_values = {
                "price": _f_price(policy, profile),
                "coverage": _f_coverage(policy, profile),
                "exclusion": _f_exclusion(policy, profile),
                "deductible": _f_deductible(policy, profile),
                "fit": _f_fit(policy, profile),
            }
            contributions = {
                key: self.weights[key] * value for key, value in f_values.items()
            }

            # 0..100 score
            total = sum(contributions.values()) * 100.0

            # Per-card breakdown shown in the UI as 0..100 ints, keyed by the
            # stable feature id (not the display label) so the frontend can
            # localise the label without touching the score data — the
            # score/breakdown must never change when the UI language does.
            breakdown = {
                key: round(f_values[key] * 100, 0)
                for key in self.weights
            }

            contrib_objs = [
                FeatureContributionDC(
                    feature=key,
                    weight=self.weights[key],
                    value=f_values[key],
                    contribution=contributions[key],
                    direction="positive" if contributions[key] >= 0.01 else "negative",
                    label=FEATURE_LABELS[key],
                )
                for key in self.weights
            ]

            scored.append(
                ScoredPolicyDC(
                    policy=policy,
                    score=round(total, 2),
                    breakdown=breakdown,
                    contributions=contrib_objs,
                    narrative=self._narrative(policy, total, f_values),
                )
            )

        scored.sort(key=lambda s: s.score, reverse=True)
        return scored

    @staticmethod
    def _narrative(policy: Policy, score: float, values: dict[str, float]) -> str:
        bits: list[str] = []
        if values["coverage"] >= 0.85:
            bits.append("provides comprehensive coverage")
        elif values["coverage"] >= 0.6:
            bits.append("provides solid coverage")
        else:
            bits.append("provides basic coverage")

        if values["exclusion"] >= 0.85:
            bits.append("with minimal exclusions")
        elif values["exclusion"] >= 0.6:
            bits.append("with reasonable exclusions")
        else:
            bits.append("with several exclusions to be aware of")

        if values["price"] >= 0.7:
            bits.append("and fits well within your budget")
        elif values["price"] >= 0.4:
            bits.append("and sits close to your budget")
        else:
            bits.append("though it sits above your budget")

        descriptor = (
            "highly recommended" if score >= 80
            else "recommended" if score >= 60
            else "a possible option"
        )
        return f"This policy is {descriptor} because it " + ", ".join(bits) + "."


def _values_by_policy(scored: Sequence[ScoredPolicyDC]) -> dict[int, dict[str, float]]:
    """Recover the exact normalised feature values used by the scorer."""
    return {
        item.policy.id: {
            contribution.feature: contribution.value
            for contribution in item.contributions
        }
        for item in scored
    }


def _rescale_single_weight(
    weights: dict[str, float], changed_feature: str, suggested_weight: float
) -> dict[str, float] | None:
    """Change one weight and proportionally rescale the remaining weights."""
    current_weight = weights[changed_feature]
    remainder = 1.0 - current_weight
    if remainder <= 0:
        return None

    scale = (1.0 - suggested_weight) / remainder
    adjusted = {
        feature: (
            suggested_weight if feature == changed_feature else weight * scale
        )
        for feature, weight in weights.items()
    }
    # Avoid floating-point drift in the API/documentation representation.
    drift = 1.0 - sum(adjusted.values())
    fallback_feature = next(
        feature for feature in adjusted if feature != changed_feature
    )
    adjusted[fallback_feature] += drift
    return adjusted


def find_counterfactual(
    scored: Sequence[ScoredPolicyDC],
    weights: dict[str, float],
    *,
    minimum_weight: float = 0.05,
    maximum_weight: float = 0.80,
    maximum_change: float = 0.50,
) -> CounterfactualExplanationDC | None:
    """Return the smallest reasonable deterministic change that flips rank 1.

    A candidate is considered within the displayed stress-test range when one
    factor can be changed by no more than 50 percentage points while remaining
    between 5% and 80%. The wider bound is intentional: the seeded catalogue's
    first policy dominates the runner-up on four factors, so a 35-point search
    produced no visible sensitivity result even though an extreme price-first
    preference does change the winner. The
    search uses one-point increments so the result maps directly to the
    existing percentage controls and is straightforward to reproduce.
    """
    if len(scored) < 2:
        return None

    normalised = normalise_weights(weights)
    current = scored[0]
    values = _values_by_policy(scored)
    candidates: list[
        tuple[float, int, int, CounterfactualExplanationDC]
    ] = []
    feature_order = list(normalised)

    lower = int(round(minimum_weight * 100))
    upper = int(round(maximum_weight * 100))
    for feature_index, feature in enumerate(feature_order):
        current_weight = normalised[feature]
        for percentage in range(lower, upper + 1):
            suggested = percentage / 100.0
            change = abs(suggested - current_weight)
            if change < 0.005 or change > maximum_change + 1e-9:
                continue

            adjusted = _rescale_single_weight(normalised, feature, suggested)
            if adjusted is None:
                continue

            projected = {
                item.policy.id: 100.0
                * sum(
                    adjusted[name] * values[item.policy.id][name]
                    for name in adjusted
                )
                for item in scored
            }
            winner = min(
                scored,
                key=lambda item: (-projected[item.policy.id], item.policy.id),
            )
            if winner.policy.id == current.policy.id:
                continue

            explanation = CounterfactualExplanationDC(
                current_policy_id=current.policy.id,
                current_policy_name=current.policy.name,
                alternative_policy_id=winner.policy.id,
                alternative_policy_name=winner.policy.name,
                changed_feature=feature,
                direction=(
                    "increase" if suggested > current_weight else "decrease"
                ),
                current_weight=round(current_weight, 4),
                suggested_weight=round(suggested, 4),
                adjusted_weights={
                    key: round(value, 4) for key, value in adjusted.items()
                },
                current_policy_score=round(projected[current.policy.id], 2),
                alternative_policy_score=round(
                    projected[winner.policy.id], 2
                ),
                score_margin=round(
                    projected[winner.policy.id] - projected[current.policy.id],
                    2,
                ),
            )
            candidates.append(
                (change, feature_index, percentage, explanation)
            )

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    return candidates[0][3]


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------
def best_pick(scored: Iterable[ScoredPolicyDC]) -> ScoredPolicyDC | None:
    """Return the highest-scoring scored policy, or None if empty."""
    iterator = iter(scored)
    try:
        return next(iterator)
    except StopIteration:
        return None
