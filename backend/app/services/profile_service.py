"""Risk-profile service.

File: backend/app/services/profile_service.py
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RiskProfile
from app.schemas.profile import RiskProfileUpdate


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_for_user(self, user_id: int) -> RiskProfile | None:
        stmt = select(RiskProfile).where(RiskProfile.user_id == user_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def upsert(self, user_id: int, payload: RiskProfileUpdate) -> RiskProfile:
        profile = await self.get_for_user(user_id)
        data = payload.model_dump()

        if profile is None:
            profile = RiskProfile(user_id=user_id, **data)
            self.db.add(profile)
        else:
            for key, value in data.items():
                setattr(profile, key, value)

        await self.db.flush()
        await self.db.refresh(profile)
        return profile
