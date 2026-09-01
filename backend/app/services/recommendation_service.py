"""Recommendation application service.

File: backend/app/services/recommendation_service.py
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.db.enums import ProductLine
from app.db.models import Recommendation
from app.recommender import (
    Recommender,
    ScoredPolicyDC,
    find_counterfactual,
    normalise_weights,
)
from app.schemas.policy import PolicyOut, ProviderOut
from app.schemas.recommendation import (
    CounterfactualExplanation,
    FeatureContribution,
    RecommendationResponse,
    ScoredPolicy,
)
from app.services.policy_service import PolicyService
from app.services.profile_service import ProfileService


class RecommendationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.policies = PolicyService(db)
        self.profiles = ProfileService(db)

    async def recommend(
        self,
        user_id: int,
        product_line: ProductLine | None = None,
        weight_override: dict[str, float] | None = None,
        top_k: int = 5,
    ) -> RecommendationResponse:
        # ---- Resolve profile (or fail clearly) ----
        profile = await self.profiles.get_for_user(user_id)
        if profile is None:
            raise ValidationError(
                "Risk profile is missing. Please complete your preferences first."
            )

        line = product_line or profile.insurance_type

        # ---- Pull candidates ----
        candidates = await self.policies.list_policies(product_line=line)
        if not candidates:
            raise NotFoundError(
                f"No active policies found for product line '{line.value}'."
            )

        # ---- Score ----
        weights = normalise_weights(weight_override or profile.weights)
        recommender = Recommender(weights=weights)
        scored = recommender.score(candidates, profile)
        top = scored[:top_k]
        counterfactual = find_counterfactual(scored, weights)

        # ---- Persist + return DTO ----
        ranked_dto = [self._to_scored_dto(s) for s in top]
        rec_record = Recommendation(
            user_id=user_id,
            product_line=line.value,
            weights=weights,
            ranked_policies=[s.model_dump(mode="json") for s in ranked_dto],
            rationale=ranked_dto[0].narrative if ranked_dto else None,
        )
        self.db.add(rec_record)
        await self.db.flush()
        await self.db.refresh(rec_record)

        return RecommendationResponse(
            id=rec_record.id,
            product_line=line,
            weights=weights,
            top_pick=ranked_dto[0],
            ranked_policies=ranked_dto,
            counterfactual=(
                CounterfactualExplanation.model_validate(
                    counterfactual.__dict__
                )
                if counterfactual
                else None
            ),
            rationale=ranked_dto[0].narrative if ranked_dto else "",
            created_at=rec_record.created_at,
        )

    # ---- Helpers ----
    @staticmethod
    def _to_scored_dto(s: ScoredPolicyDC) -> ScoredPolicy:
        provider_out = (
            ProviderOut.model_validate(s.policy.provider) if s.policy.provider else None
        )
        policy_out = PolicyOut.model_validate(s.policy)
        # Attach provider manually because the relationship may not autoload.
        if provider_out:
            policy_out = policy_out.model_copy(update={"provider": provider_out})

        contributions = [
            FeatureContribution(
                feature=c.feature,
                weight=round(c.weight, 4),
                value=round(c.value, 4),
                contribution=round(c.contribution, 4),
                direction=c.direction,
                label=c.label,
            )
            for c in s.contributions
        ]

        return ScoredPolicy(
            policy=policy_out,
            score=s.score,
            breakdown=s.breakdown,
            contributions=contributions,
            narrative=s.narrative,
        )
