"""Recommendation request and response schemas.

File: backend/app/schemas/recommendation.py
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import ProductLine
from app.schemas.policy import PolicyOut


class RecommendationRequest(BaseModel):
    """Optional explicit request payload; otherwise the user's stored
    risk profile is used."""

    product_line: ProductLine | None = None
    weights: dict[str, float] | None = None
    top_k: int = Field(default=5, ge=1, le=10)


class FeatureContribution(BaseModel):
    """One row of the SHAP-style narrative shown in the UI explainability panel."""

    feature: str
    weight: float
    value: float
    contribution: float
    direction: str = Field(description="'positive' or 'negative'")
    label: str = Field(description="Human-readable feature label")


class ScoredPolicy(BaseModel):
    """A single policy in the ranked list."""

    policy: PolicyOut
    score: float = Field(ge=0.0, le=100.0)
    breakdown: dict[str, float] = Field(
        description="Score breakdown displayed in the per-policy card "
                    "(price, coverage, exclusions, deductible, match)"
    )
    contributions: list[FeatureContribution]
    narrative: str


class CounterfactualExplanation(BaseModel):
    """Deterministic one-factor sensitivity result for the current ranking."""

    current_policy_id: int
    current_policy_name: str
    alternative_policy_id: int
    alternative_policy_name: str
    changed_feature: str
    direction: str = Field(pattern="^(increase|decrease)$")
    current_weight: float = Field(ge=0.0, le=1.0)
    suggested_weight: float = Field(ge=0.0, le=1.0)
    adjusted_weights: dict[str, float]
    current_policy_score: float = Field(ge=0.0, le=100.0)
    alternative_policy_score: float = Field(ge=0.0, le=100.0)
    score_margin: float = Field(ge=0.0)


class RecommendationResponse(BaseModel):
    """Top-level response returned by ``POST /recommend``."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    product_line: ProductLine
    weights: dict[str, float]
    top_pick: ScoredPolicy
    ranked_policies: list[ScoredPolicy]
    counterfactual: CounterfactualExplanation | None = None
    rationale: str
    created_at: datetime | None = None
