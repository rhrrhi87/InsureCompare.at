"""Refresh-token session lifecycle: issue, rotate, revoke.

File: backend/app/services/session_service.py

The refresh JWT itself proves who the caller claims to be (signature +
expiry, checked by ``decode_token``); the ``Session`` row is what makes that
claim *revocable* — logout, or reuse of an already-rotated refresh token,
invalidates it even though the JWT signature is still technically valid
until its ``exp``.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as DBSession

from app.core.config import settings
from app.core.exceptions import UnauthorisedError
from app.core.security import hash_token
from app.db.models import Session


def _as_utc(value: datetime) -> datetime:
    """Normalise a datetime read back from the DB to be timezone-aware.

    SQLite (used by the test suite) has no native tz-aware timestamp type,
    so ``DateTime(timezone=True)`` columns round-trip as naive datetimes
    there even though PostgreSQL returns real aware datetimes for the same
    column. Comparing a naive value against ``datetime.now(timezone.utc)``
    raises ``TypeError`` — this makes the comparison work on both backends.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class SessionService:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    async def create(self, user_id: int, refresh_token: str) -> Session:
        session = Session(
            user_id=user_id,
            refresh_token_hash=hash_token(refresh_token),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.JWT_REFRESH_TOKEN_DAYS),
            revoked=False,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_active(self, refresh_token: str) -> Session:
        """Return the active (non-revoked, non-expired) session matching a
        refresh token, or raise ``UnauthorisedError``."""
        stmt = select(Session).where(
            Session.refresh_token_hash == hash_token(refresh_token)
        )
        session = (await self.db.execute(stmt)).scalar_one_or_none()
        if session is None or session.revoked:
            raise UnauthorisedError("Session has been revoked")
        if _as_utc(session.expires_at) < datetime.now(UTC):
            raise UnauthorisedError("Session has expired")
        return session

    async def revoke(self, session: Session) -> None:
        session.revoked = True
        await self.db.flush()

    async def revoke_by_token(self, refresh_token: str) -> None:
        stmt = select(Session).where(
            Session.refresh_token_hash == hash_token(refresh_token)
        )
        session = (await self.db.execute(stmt)).scalar_one_or_none()
        if session is not None:
            session.revoked = True
            await self.db.flush()
