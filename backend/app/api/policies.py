"""Policy + provider catalogue endpoints.

File: backend/app/api/policies.py
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_only, current_user
from app.db.enums import ProductLine
from app.db.models import User
from app.db.session import get_db
from app.schemas.policy import (
    ClauseOut,
    PolicyCreate,
    PolicyOut,
    PolicyUpdate,
    ProviderCreate,
    ProviderOut,
    ProviderUpdate,
)
from app.services.admin_service import AdminService
from app.services.policy_service import PolicyService

router = APIRouter(tags=["policies"])


# ---- Providers -----------------------------------------------------------------
@router.get(
    "/providers",
    response_model=list[ProviderOut],
    summary="List active insurance providers",
)
async def list_providers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> list[ProviderOut]:
    providers = await PolicyService(db).list_providers()
    return [ProviderOut.model_validate(p) for p in providers]


@router.post(
    "/providers",
    response_model=ProviderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new provider (admin only)",
)
async def create_provider(
    payload: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
) -> ProviderOut:
    return ProviderOut.model_validate(await PolicyService(db).create_provider(payload))


@router.patch(
    "/providers/{provider_id}",
    response_model=ProviderOut,
    summary="Update a provider (admin only)",
)
async def update_provider(
    provider_id: int,
    payload: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
) -> ProviderOut:
    return ProviderOut.model_validate(
        await PolicyService(db).update_provider(provider_id, payload)
    )


@router.post(
    "/providers/{provider_id}/deactivate",
    response_model=ProviderOut,
    summary="Deactivate a provider (admin only) — never hard-deleted",
)
async def deactivate_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
) -> ProviderOut:
    return ProviderOut.model_validate(
        await PolicyService(db).set_provider_active(provider_id, active=False)
    )


@router.post(
    "/providers/{provider_id}/reactivate",
    response_model=ProviderOut,
    summary="Reactivate a provider (admin only)",
)
async def reactivate_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
) -> ProviderOut:
    return ProviderOut.model_validate(
        await PolicyService(db).set_provider_active(provider_id, active=True)
    )


# ---- Policies ------------------------------------------------------------------
@router.get(
    "/policies",
    response_model=list[PolicyOut],
    summary="List policies (optionally filtered by product line)",
)
async def list_policies(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
    product_line: ProductLine | None = Query(default=None),
    active_only: bool = Query(default=True),
) -> list[PolicyOut]:
    policies = await PolicyService(db).list_policies(product_line, active_only)
    return [PolicyOut.model_validate(p) for p in policies]


@router.get(
    "/policies/{policy_id}",
    response_model=PolicyOut,
    summary="Retrieve a single policy",
)
async def get_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> PolicyOut:
    return PolicyOut.model_validate(await PolicyService(db).get_policy(policy_id))


@router.post(
    "/policies",
    response_model=PolicyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new policy (admin only)",
)
async def create_policy(
    payload: PolicyCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_only),
) -> PolicyOut:
    policy = await PolicyService(db).create_policy(payload)
    await AdminService(db).record_action(
        actor_id=admin.id, actor_email=admin.email, action="POLICY_CREATED",
        entity_type="policy", entity_id=policy.id,
    )
    return PolicyOut.model_validate(policy)


@router.patch(
    "/policies/{policy_id}",
    response_model=PolicyOut,
    summary="Update an existing policy (admin only)",
)
async def update_policy(
    policy_id: int,
    payload: PolicyUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_only),
) -> PolicyOut:
    policy = await PolicyService(db).update_policy(policy_id, payload)
    await AdminService(db).record_action(
        actor_id=admin.id, actor_email=admin.email, action="POLICY_UPDATED",
        entity_type="policy", entity_id=policy_id,
    )
    return PolicyOut.model_validate(policy)


@router.post(
    "/policies/{policy_id}/retire",
    response_model=PolicyOut,
    summary="Retire a policy (admin only) — never hard-deleted",
)
async def retire_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_only),
) -> PolicyOut:
    policy = await PolicyService(db).retire_policy(policy_id)
    await AdminService(db).record_action(
        actor_id=admin.id, actor_email=admin.email, action="POLICY_RETIRED",
        entity_type="policy", entity_id=policy_id,
    )
    return PolicyOut.model_validate(policy)


@router.post(
    "/policies/{policy_id}/reactivate",
    response_model=PolicyOut,
    summary="Reactivate a retired policy (admin only)",
)
async def reactivate_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
) -> PolicyOut:
    return PolicyOut.model_validate(await PolicyService(db).reactivate_policy(policy_id))


@router.get(
    "/policies/{policy_id}/clauses",
    response_model=list[ClauseOut],
    summary="Source-evidence clauses backing a catalogue policy, if any",
)
async def get_policy_clauses(
    policy_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(current_user),
) -> list[ClauseOut]:
    clauses = await PolicyService(db).get_clauses_for_policy(policy_id)
    return [ClauseOut.model_validate(c) for c in clauses]
