"""Risk-profile schemas.

File: backend/app/schemas/profile.py
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import (
    CoverageLevel,
    DeductiblePreference,
    ProductLine,
    RiskTolerance,
)


class WeightConfig(BaseModel):
    """Optional override for the default scoring weights.

    Values are normalised to sum to 1.0 in the recommender service if needed.
    Defaults match the production UI (Price 25 / Coverage 30 / Exclusion 20 /
    Deductible 10 / Preference 15).
    """

    price: float = Field(default=0.25, ge=0.0, le=1.0)
    coverage: float = Field(default=0.30, ge=0.0, le=1.0)
    exclusion: float = Field(default=0.20, ge=0.0, le=1.0)
    deductible: float = Field(default=0.10, ge=0.0, le=1.0)
    fit: float = Field(default=0.15, ge=0.0, le=1.0)


class RiskProfileBase(BaseModel):
    insurance_type: ProductLine = ProductLine.CAR
    monthly_budget_eur: float = Field(default=100.0, ge=0.0)
    risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM
    coverage_level: CoverageLevel = CoverageLevel.STANDARD
    deductible_preference: DeductiblePreference = DeductiblePreference.MEDIUM
    household_size: int = Field(default=1, ge=1, le=20)
    property_value_eur: float | None = Field(default=None, ge=0.0)
    required_coverages: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)


class RiskProfileUpdate(RiskProfileBase):
    """Same as base; lets clients PUT the full profile in one call."""


class RiskProfileOut(RiskProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
