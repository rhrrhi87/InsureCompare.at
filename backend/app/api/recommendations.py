"""Recommendation endpoint.

File: backend/app/api/recommendations.py
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.admin_service import AdminService
from app.services.recommendation_service import RecommendationService

router = APIRouter(tags=["recommendations"])


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Produce a ranked, explained recommendation for the current user",
)
async def recommend(
    payload: RecommendationRequest = RecommendationRequest(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> RecommendationResponse:
    result = await RecommendationService(db).recommend(
        user_id=user.id,
        product_line=payload.product_line,
        weight_override=payload.weights,
        top_k=payload.top_k,
    )
    await AdminService(db).record_action(
        actor_id=user.id, actor_email=user.email, action="RECOMMENDATION_GENERATED",
        entity_type="recommendation", entity_id=result.id,
        payload={"product_line": result.product_line.value},
    )
    return result
