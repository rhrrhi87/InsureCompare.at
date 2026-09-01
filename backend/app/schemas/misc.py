"""Upload, comparison and admin schemas.

File: backend/app/schemas/misc.py
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import ClauseType, UploadStatus
from app.schemas.policy import PolicyOut


class ExtractedClauseOut(BaseModel):
    clause_type: ClauseType
    label: str | None = None
    text: str
    confidence: float
    page_number: int | None = None


class ExtractedDocument(BaseModel):
    """Structured extraction result for a single uploaded document."""

    detected_provider: str | None = None
    detected_product_line: str | None = None
    monthly_premium_eur: float | None = None
    annual_premium_eur: float | None = None
    deductible_eur: float | None = None
    coverage_limit_eur: float | None = None
    coverages: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    clauses: list[ExtractedClauseOut] = Field(default_factory=list)
    raw_text_excerpt: str | None = Field(default=None, max_length=2000)


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    filename: str
    content_type: str
    size_bytes: int
    status: UploadStatus
    ocr_confidence: float | None = None
    extracted: ExtractedDocument | None = None
    error_message: str | None = None
    created_at: datetime


class CompareRequest(BaseModel):
    policy_ids: list[int] = Field(min_length=2, max_length=3)


class CompareSummary(BaseModel):
    cheapest_monthly_eur: float
    average_monthly_eur: float
    within_budget_count: int
    low_risk_count: int


class CompareResponse(BaseModel):
    policies: list[PolicyOut]
    summary: CompareSummary


# ---- Admin ----
class AdminStats(BaseModel):
    total_users: int
    total_policies: int
    total_uploads: int
    total_recommendations: int


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    actor_email: str | None
    action: str
    entity_type: str | None
    entity_id: int | None
    payload: dict | None = None
    created_at: datetime
