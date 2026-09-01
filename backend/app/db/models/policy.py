"""Policy catalogue and extracted clauses.

File: backend/app/db/models/policy.py
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, str_enum
from app.db.enums import ClauseType, ExtractionMethod, ProductLine, RiskLevel

if TYPE_CHECKING:
    from app.db.models.provider import Provider
    from app.db.models.upload import Upload


class Policy(Base, TimestampMixin):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    product_line: Mapped[ProductLine] = mapped_column(
        str_enum(ProductLine, name="product_line", create_type=False), nullable=False, index=True
    )

    # Pricing
    monthly_premium_eur: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    annual_premium_eur: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    deductible_eur: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    coverage_limit_eur: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    # Quality / risk
    risk_level: Mapped[RiskLevel] = mapped_column(
        str_enum(RiskLevel, name="risk_level"), default=RiskLevel.MEDIUM, nullable=False
    )

    # Structured content (denormalised JSON for fast read; canonical clauses live below)
    coverage_items: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    additional_features: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    exclusions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ---- Source provenance (spec: every catalogue product must support
    # provenance metadata for evidence traceability). Left null for
    # demonstration-only catalogue rows added before a real public document
    # was cited — see docs/DATA_SOURCES.md. Never fabricate these values.
    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    document_title: Mapped[str | None] = mapped_column(String(255))
    document_type: Mapped[str | None] = mapped_column(String(30))  # e.g. "IPID", "AVB"
    source_url: Mapped[str | None] = mapped_column(String(512))
    source_organisation: Mapped[str | None] = mapped_column(String(180))
    retrieval_date: Mapped[date | None] = mapped_column(Date)
    last_reviewed_date: Mapped[date | None] = mapped_column(Date)
    document_language: Mapped[str] = mapped_column(String(5), default="de", nullable=False)

    # ---- Relationships ----
    provider: Mapped[Provider] = relationship(back_populates="policies")
    clauses: Mapped[list[Clause]] = relationship(
        back_populates="policy",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Policy id={self.id} provider={self.provider_id} "
            f"name={self.name!r} line={self.product_line.value}>"
        )


class Clause(Base, TimestampMixin):
    """Individual clause extracted from a policy document by the NLP pipeline."""

    __tablename__ = "clauses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Exactly one of policy_id / upload_id is set: a clause either belongs to
    # a catalogue policy (admin-entered/seeded evidence) or to a specific
    # user upload (personal document analysis) — never both, never neither.
    policy_id: Mapped[int | None] = mapped_column(
        ForeignKey("policies.id", ondelete="CASCADE"), index=True
    )
    upload_id: Mapped[int | None] = mapped_column(
        ForeignKey("uploads.id", ondelete="CASCADE"), index=True
    )
    clause_type: Mapped[ClauseType] = mapped_column(
        str_enum(ClauseType, name="clause_type"), nullable=False, index=True
    )
    label: Mapped[str | None] = mapped_column(String(180))
    # Original extracted text, verbatim — never translated or edited. The UI
    # may show a localised concept label alongside it, but this field is the
    # source-of-truth evidence and must never be overwritten by a translation.
    text: Mapped[str] = mapped_column(Text, nullable=False)
    document_language: Mapped[str] = mapped_column(String(5), default="de", nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=1.0, nullable=False)
    extraction_method: Mapped[ExtractionMethod] = mapped_column(
        str_enum(ExtractionMethod, name="extraction_method"),
        default=ExtractionMethod.SEED,
        nullable=False,
    )

    # Embedding stored as JSON for portability; can be migrated to pgvector
    # without changing the application code (see Alembic migration 002).
    embedding: Mapped[list[float] | None] = mapped_column(JSON)

    policy: Mapped[Policy | None] = relationship(back_populates="clauses")
    upload: Mapped[Upload | None] = relationship()

    def __repr__(self) -> str:
        return f"<Clause id={self.id} policy={self.policy_id} type={self.clause_type.value}>"
