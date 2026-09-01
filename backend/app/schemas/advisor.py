"""AI Policy Advisor schemas (evidence-grounded, RAG-based).

File: backend/app/schemas/advisor.py

See docs/AI_ADVISOR_ARCHITECTURE.md for the full design. Two schemas
(`AdvisorResponse`, `AdvisorSummary`) are the *validated structured output
contract* the LLM provider must fill in — never free-form text. Gemini's
own `evidence_ids` are never trusted directly; the service layer filters
them against the real, backend-supplied allowed set before anything here
reaches the client (see app/services/advisor_service.py).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class AdvisorResponse(BaseModel):
    """Raw structured output requested from the LLM for a single question."""

    answer: str
    supported: bool
    evidence_ids: list[int] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    attention_points: list[str] = Field(default_factory=list)


class AdvisorSummary(BaseModel):
    """Raw structured output requested from the LLM for a document overview.

    Every field is optional/omittable — the model is instructed not to
    populate a field it has no evidence for, and the service layer never
    invents a default value for a missing one.
    """

    insurer: str | None = None
    insurance_type: str | None = None
    product_name: str | None = None
    main_coverages: list[str] = Field(default_factory=list)
    important_exclusions: list[str] = Field(default_factory=list)
    deductible: str | None = None
    coverage_limits: str | None = None
    territorial_scope: str | None = None
    major_conditions: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    attention_points: list[str] = Field(default_factory=list)
    evidence_ids: list[int] = Field(default_factory=list)


class AdvisorEvidenceRef(BaseModel):
    """A single piece of source evidence, rendered directly from PostgreSQL
    — never from LLM-generated text (Part 10 / Part 9 requirement)."""

    clause_id: int
    clause_type: str
    text: str
    page_number: int | None = None
    confidence: float
    provenance: str


class AdvisorDocumentRef(BaseModel):
    """Document-level context shown alongside Source Evidence (Part 10):
    insurer/product line as detected by the existing deterministic NLP
    extractor (never Gemini-generated), and the real uploaded filename as
    the document title — this project does not capture a separate
    human-authored "document title" for user uploads."""

    document_title: str
    detected_insurer: str | None = None
    detected_product_line: str | None = None


class AdvisorAnswer(BaseModel):
    """API response for a single Advisor question."""

    answer: str
    supported: bool
    key_points: list[str] = Field(default_factory=list)
    attention_points: list[str] = Field(default_factory=list)
    evidence: list[AdvisorEvidenceRef] = Field(default_factory=list)
    document: AdvisorDocumentRef | None = None
    available: bool = True
    unavailable_reason: str | None = None


class AdvisorSummaryOut(BaseModel):
    """API response for the document overview / policy-overview panel."""

    summary: AdvisorSummary | None
    evidence: list[AdvisorEvidenceRef] = Field(default_factory=list)
    document: AdvisorDocumentRef | None = None
    available: bool = True
    unavailable_reason: str | None = None


class AdvisorQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    language: str = Field(default="de", pattern="^(de|en)$")
