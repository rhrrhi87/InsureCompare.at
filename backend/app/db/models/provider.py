"""Insurance provider catalogue.

File: backend/app/db/models/provider.py
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.policy import Policy


class Provider(Base, TimestampMixin):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    country: Mapped[str] = mapped_column(String(2), default="AT", nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(512))
    rating_score: Mapped[float] = mapped_column(Numeric(3, 1), default=8.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    policies: Mapped[list[Policy]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Provider id={self.id} name={self.name!r}>"
