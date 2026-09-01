"""Side-by-side policy comparison service.

File: backend/app/services/compare_service.py
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.db.enums import RiskLevel
from app.schemas.misc import CompareResponse, CompareSummary
from app.schemas.policy import PolicyOut, ProviderOut
from app.services.policy_service import PolicyService


class CompareService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.policies = PolicyService(db)

    async def compare(
        self,
        policy_ids: list[int],
        monthly_budget_eur: float | None = None,
    ) -> CompareResponse:
        if not (2 <= len(policy_ids) <= 3):
            raise ValidationError("Compare 2 or 3 policies at a time.")

        rows = await self.policies.get_policies_by_ids(policy_ids)
        if len(rows) != len(policy_ids):
            raise ValidationError("One or more policy IDs are invalid.")

        # Maintain caller-supplied order
        ordered = sorted(rows, key=lambda p: policy_ids.index(p.id))

        monthly_values = [float(p.monthly_premium_eur) for p in ordered]
        cheapest = min(monthly_values)
        average = sum(monthly_values) / len(monthly_values)

        within_budget = (
            sum(1 for v in monthly_values if monthly_budget_eur is None or v <= monthly_budget_eur)
            if monthly_budget_eur is not None
            else len(monthly_values)
        )
        low_risk = sum(1 for p in ordered if p.risk_level == RiskLevel.LOW)

        out_policies: list[PolicyOut] = []
        for p in ordered:
            policy_out = PolicyOut.model_validate(p)
            if p.provider:
                policy_out = policy_out.model_copy(
                    update={"provider": ProviderOut.model_validate(p.provider)}
                )
            out_policies.append(policy_out)

        return CompareResponse(
            policies=out_policies,
            summary=CompareSummary(
                cheapest_monthly_eur=round(cheapest, 2),
                average_monthly_eur=round(average, 2),
                within_budget_count=within_budget,
                low_risk_count=low_risk,
            ),
        )
