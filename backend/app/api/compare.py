"""Side-by-side policy comparison endpoint.

File: backend/app/api/compare.py
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.misc import CompareRequest, CompareResponse
from app.services.compare_service import CompareService
from app.services.profile_service import ProfileService

router = APIRouter(tags=["compare"])


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare 2-3 policies side by side",
)
async def compare(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> CompareResponse:
    profile = await ProfileService(db).get_for_user(user.id)
    monthly_budget = float(profile.monthly_budget_eur) if profile else None
    return await CompareService(db).compare(
        policy_ids=payload.policy_ids,
        monthly_budget_eur=monthly_budget,
    )
