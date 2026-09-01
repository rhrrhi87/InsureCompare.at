"""Policy + provider catalogue service.

File: backend/app/services/policy_service.py
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.db.enums import ProductLine
from app.db.models import Clause, Policy, Provider
from app.schemas.policy import (
    PolicyCreate,
    PolicyUpdate,
    ProviderCreate,
    ProviderUpdate,
)


class PolicyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---- Providers ----
    async def list_providers(self) -> list[Provider]:
        stmt = select(Provider).order_by(Provider.name)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_provider(self, provider_id: int) -> Provider:
        provider = await self.db.get(Provider, provider_id)
        if not provider:
            raise NotFoundError("Provider not found")
        return provider

    async def create_provider(self, payload: ProviderCreate) -> Provider:
        provider = Provider(**payload.model_dump())
        self.db.add(provider)
        await self.db.flush()
        await self.db.refresh(provider)
        return provider

    async def update_provider(self, provider_id: int, payload: ProviderUpdate) -> Provider:
        provider = await self.get_provider(provider_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(provider, key, value)
        await self.db.flush()
        await self.db.refresh(provider)
        return provider

    async def set_provider_active(self, provider_id: int, active: bool) -> Provider:
        """Deactivate/reactivate a provider.

        Providers are never hard-deleted: doing so would cascade-delete
        their policies, which could be referenced by historical
        recommendations that must remain reproducible (spec: never destroy
        data needed to reproduce a past recommendation).
        """
        provider = await self.get_provider(provider_id)
        provider.is_active = active
        await self.db.flush()
        await self.db.refresh(provider)
        return provider

    # ---- Policies ----
    async def list_policies(
        self,
        product_line: ProductLine | None = None,
        active_only: bool = True,
    ) -> list[Policy]:
        stmt = select(Policy).options(selectinload(Policy.provider))
        if active_only:
            stmt = stmt.where(Policy.is_active.is_(True))
        if product_line is not None:
            stmt = stmt.where(Policy.product_line == product_line)
        stmt = stmt.order_by(Policy.product_line, Policy.monthly_premium_eur)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_policy(self, policy_id: int) -> Policy:
        stmt = (
            select(Policy)
            .options(selectinload(Policy.provider))
            .where(Policy.id == policy_id)
        )
        result = await self.db.execute(stmt)
        policy = result.scalar_one_or_none()
        if not policy:
            raise NotFoundError("Policy not found")
        return policy

    async def get_policies_by_ids(self, policy_ids: list[int]) -> list[Policy]:
        if not policy_ids:
            return []
        stmt = (
            select(Policy)
            .options(selectinload(Policy.provider))
            .where(Policy.id.in_(policy_ids))
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_policy(self, payload: PolicyCreate) -> Policy:
        policy = Policy(**payload.model_dump())
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        return await self.get_policy(policy.id)

    async def update_policy(self, policy_id: int, payload: PolicyUpdate) -> Policy:
        policy = await self.get_policy(policy_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(policy, key, value)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def retire_policy(self, policy_id: int) -> Policy:
        """Retire a policy: excluded from new comparisons/recommendations,
        but the row (and any recommendation snapshots referencing it) is
        preserved so past results stay reproducible. Never hard-deleted."""
        policy = await self.get_policy(policy_id)
        policy.is_active = False
        policy.retired_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(policy)
        return await self.get_policy(policy.id)

    async def reactivate_policy(self, policy_id: int) -> Policy:
        policy = await self.get_policy(policy_id)
        policy.is_active = True
        policy.retired_at = None
        await self.db.flush()
        await self.db.refresh(policy)
        return await self.get_policy(policy.id)

    async def get_clauses_for_policy(self, policy_id: int) -> list[Clause]:
        """Source-evidence clauses backing a catalogue policy, if any.

        Demonstration catalogue entries (``is_demo_data=True``) generally
        have none — that absence is shown honestly in the UI rather than
        being backed by fabricated clause text.
        """
        await self.get_policy(policy_id)  # 404s if missing
        stmt = (
            select(Clause)
            .where(Clause.policy_id == policy_id)
            .order_by(Clause.page_number, Clause.id)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    # ---- Stats ----
    async def count_policies(self, product_line: ProductLine | None = None) -> int:
        stmt = select(func.count(Policy.id))
        if product_line is not None:
            stmt = stmt.where(Policy.product_line == product_line)
        return int((await self.db.execute(stmt)).scalar_one())
