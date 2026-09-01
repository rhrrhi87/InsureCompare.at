"""Recommendation results and admin audit log.

File: backend/app/db/models/recommendation.py
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Recommendation(Base, TimestampMixin):
    """Persisted recommendation including the SHAP-style rationale."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # The product line for which this recommendation was produced
    product_line: Mapped[str] = mapped_column(String(32), nullable=False)

    # Snapshot of the weights actually used (auditable)
    weights: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Ordered list of {policy_id, score, breakdown, contributions, narrative}
    ranked_policies: Mapped[list[dict]] = mapped_column(JSON, nullable=False)

    # Free-text top-line rationale shown on the UI's best-match card.
    rationale: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} user={self.user_id} line={self.product_line!r}>"


class AuditLog(Base, TimestampMixin):
    """Append-only audit trail of high-value actions (admin + recommendations)."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    actor_email: Mapped[str | None] = mapped_column(String(254))
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(60))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action!r} actor={self.actor_id}>"
