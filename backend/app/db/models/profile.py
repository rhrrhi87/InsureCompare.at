"""User risk profile - what the user wants in a policy.

File: backend/app/db/models/profile.py
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, str_enum
from app.db.enums import (
    CoverageLevel,
    DeductiblePreference,
    ProductLine,
    RiskTolerance,
)

if TYPE_CHECKING:
    from app.db.models.user import User


class RiskProfile(Base, TimestampMixin):
    """Persisted user preferences feeding the recommendation engine."""

    __tablename__ = "risk_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_risk_profiles_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Preferences
    insurance_type: Mapped[ProductLine] = mapped_column(
        str_enum(ProductLine, name="product_line"), default=ProductLine.CAR, nullable=False
    )
    monthly_budget_eur: Mapped[float] = mapped_column(
        Numeric(8, 2), default=100.00, nullable=False
    )
    risk_tolerance: Mapped[RiskTolerance] = mapped_column(
        str_enum(RiskTolerance, name="risk_tolerance"),
        default=RiskTolerance.MEDIUM,
        nullable=False,
    )
    coverage_level: Mapped[CoverageLevel] = mapped_column(
        str_enum(CoverageLevel, name="coverage_level"),
        default=CoverageLevel.STANDARD,
        nullable=False,
    )
    deductible_preference: Mapped[DeductiblePreference] = mapped_column(
        str_enum(DeductiblePreference, name="deductible_preference"),
        default=DeductiblePreference.MEDIUM,
        nullable=False,
    )

    household_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    property_value_eur: Mapped[float | None] = mapped_column(Numeric(12, 2))
    required_coverages: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    # Custom scoring weights (override defaults). Must sum to ~1.
    weights: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # ---- Relationships ----
    user: Mapped[User] = relationship(back_populates="risk_profile")

    def __repr__(self) -> str:
        return (
            f"<RiskProfile id={self.id} user={self.user_id} "
            f"line={self.insurance_type.value}>"
        )
