"""Admin service.

File: backend/app/services/admin_service.py
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, Policy, Recommendation, Upload, User
from app.schemas.misc import AdminStats


class AdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def stats(self) -> AdminStats:
        users = await self.db.scalar(select(func.count(User.id)))
        policies = await self.db.scalar(select(func.count(Policy.id)))
        uploads = await self.db.scalar(select(func.count(Upload.id)))
        recs = await self.db.scalar(select(func.count(Recommendation.id)))
        return AdminStats(
            total_users=int(users or 0),
            total_policies=int(policies or 0),
            total_uploads=int(uploads or 0),
            total_recommendations=int(recs or 0),
        )

    async def record_action(
        self,
        actor_id: int | None,
        actor_email: str | None,
        action: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        payload: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            ip_address=ip_address,
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def list_audit_log(self, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_uploads(self, limit: int = 100) -> list[Upload]:
        stmt = select(Upload).order_by(Upload.created_at.desc()).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())
