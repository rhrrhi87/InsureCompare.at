"""User risk-profile endpoints.

File: backend/app/api/profiles.py
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.core.exceptions import NotFoundError, domain_to_http
from app.db.models import User
from app.db.session import get_db
from app.schemas.profile import RiskProfileOut, RiskProfileUpdate
from app.services.admin_service import AdminService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get(
    "/me",
    response_model=RiskProfileOut,
    summary="Get the current user's risk profile",
)
async def get_my_profile(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskProfileOut:
    profile = await ProfileService(db).get_for_user(user.id)
    if profile is None:
        raise domain_to_http(NotFoundError("Risk profile not yet set"))
    return RiskProfileOut.model_validate(profile)


@router.put(
    "/me",
    response_model=RiskProfileOut,
    summary="Create or update the current user's risk profile",
)
async def upsert_my_profile(
    payload: RiskProfileUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskProfileOut:
    existing = await ProfileService(db).get_for_user(user.id)
    weights_changed = existing is not None and existing.weights != payload.weights

    profile = await ProfileService(db).upsert(user.id, payload)

    if weights_changed:
        await AdminService(db).record_action(
            actor_id=user.id, actor_email=user.email, action="WEIGHTS_CHANGED",
            entity_type="risk_profile", entity_id=profile.id,
            payload={"weights": payload.weights},
        )
    return RiskProfileOut.model_validate(profile)
