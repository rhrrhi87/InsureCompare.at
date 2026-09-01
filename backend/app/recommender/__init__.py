"""Recommendation engine + SHAP-style explainer."""
from app.recommender.scorer import (
    DEFAULT_WEIGHTS,
    FEATURE_LABELS,
    CounterfactualExplanationDC,
    FeatureContributionDC,
    Recommender,
    ScoredPolicyDC,
    best_pick,
    find_counterfactual,
    normalise_weights,
)

__all__ = [
    "DEFAULT_WEIGHTS",
    "FEATURE_LABELS",
    "CounterfactualExplanationDC",
    "FeatureContributionDC",
    "Recommender",
    "ScoredPolicyDC",
    "best_pick",
    "find_counterfactual",
    "normalise_weights",
]
