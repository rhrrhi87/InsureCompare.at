"""Provider and Policy schemas.

File: backend/app/schemas/policy.py
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import ClauseType, ExtractionMethod, ProductLine, RiskLevel


# ---- Provider ----
class ProviderBase(BaseModel):
    name: str = Field(max_length=120)
    country: str = Field(default="AT", min_length=2, max_length=2)
    logo_url: str | None = Field(default=None, max_length=512)
    rating_score: float = Field(default=8.0, ge=0.0, le=10.0)
    is_active: bool = True


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    logo_url: str | None = Field(default=None, max_length=512)
    rating_score: float | None = Field(default=None, ge=0.0, le=10.0)
    is_active: bool | None = None


class ProviderOut(ProviderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ---- Policy ----
class PolicyBase(BaseModel):
    name: str = Field(max_length=180)
    product_line: ProductLine
    monthly_premium_eur: float = Field(ge=0.0)
    annual_premium_eur: float = Field(ge=0.0)
    deductible_eur: float = Field(default=0.0, ge=0.0)
    coverage_limit_eur: float = Field(ge=0.0)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    coverage_items: list[str] = Field(default_factory=list)
    additional_features: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    description: str | None = None
    is_active: bool = True

    # ---- Source provenance (see docs/DATA_SOURCES.md) ----
    # Defaults to demonstration data: true until an admin cites a real
    # public IPID/AVB document for this entry. Never set source fields to
    # values that were not actually verified against a real document.
    is_demo_data: bool = True
    document_title: str | None = Field(default=None, max_length=255)
    document_type: str | None = Field(default=None, max_length=30)
    source_url: str | None = Field(default=None, max_length=512)
    source_organisation: str | None = Field(default=None, max_length=180)
    retrieval_date: date | None = None
    last_reviewed_date: date | None = None
    document_language: str = Field(default="de", min_length=2, max_length=5)


class PolicyCreate(PolicyBase):
    provider_id: int


class PolicyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=180)
    monthly_premium_eur: float | None = Field(default=None, ge=0.0)
    annual_premium_eur: float | None = Field(default=None, ge=0.0)
    deductible_eur: float | None = Field(default=None, ge=0.0)
    coverage_limit_eur: float | None = Field(default=None, ge=0.0)
    risk_level: RiskLevel | None = None
    coverage_items: list[str] | None = None
    additional_features: list[str] | None = None
    exclusions: list[str] | None = None
    description: str | None = None
    is_demo_data: bool | None = None
    document_title: str | None = Field(default=None, max_length=255)
    document_type: str | None = Field(default=None, max_length=30)
    source_url: str | None = Field(default=None, max_length=512)
    source_organisation: str | None = Field(default=None, max_length=180)
    retrieval_date: date | None = None
    last_reviewed_date: date | None = None
    document_language: str | None = Field(default=None, min_length=2, max_length=5)


class PolicyOut(PolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    provider: ProviderOut | None = None
    created_at: datetime
    retired_at: datetime | None = None


class ClauseOut(BaseModel):
    """A single piece of source evidence backing a catalogue policy."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    clause_type: ClauseType
    label: str | None
    text: str
    document_language: str
    page_number: int | None
    confidence: float
    extraction_method: ExtractionMethod
