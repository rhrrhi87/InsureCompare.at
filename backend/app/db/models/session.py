"""Refresh-token sessions (enables rotation + revocation).

File: backend/app/db/models/session.py

The access token stays a stateless, short-lived JWT. The refresh token is
also a JWT (so it is self-describing and signed), but its *validity* is
additionally gated on a matching, non-revoked row here — that is what makes
rotation-on-use and logout actually revoke a token instead of merely
discarding it client-side. Only a SHA-256 hash of the refresh token is
stored, never the token itself.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship()

    def __repr__(self) -> str:
        return f"<Session id={self.id} user={self.user_id} revoked={self.revoked}>"
