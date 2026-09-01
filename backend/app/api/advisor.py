"""AI Policy Advisor endpoints — evidence-grounded RAG over one upload.

File: backend/app/api/advisor.py

Both endpoints re-use UploadService.get_for_user, so a user can only ever
run the Advisor against their own uploaded document (document isolation is
enforced at both the ownership layer here and the retrieval layer in
advisor_service, which additionally scopes every clause query to the
requested upload_id).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.advisor import AdvisorAnswer, AdvisorQuestionRequest, AdvisorSummaryOut
from app.services import advisor_service
from app.services.upload_service import UploadService

router = APIRouter(prefix="/uploads", tags=["advisor"])


@router.get(
    "/{upload_id}/advisor/summary",
    response_model=AdvisorSummaryOut,
    summary="AI Policy Advisor: evidence-grounded document overview (cached)",
)
async def get_advisor_summary(
    upload_id: int,
    language: str = Query(default="de", pattern="^(de|en)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AdvisorSummaryOut:
    upload = await UploadService(db).get_for_user(user.id, upload_id)
    return await advisor_service.get_or_generate_summary(db, upload=upload, language=language)


@router.post(
    "/{upload_id}/advisor/ask",
    response_model=AdvisorAnswer,
    summary="AI Policy Advisor: ask a question about this document (RAG)",
)
async def ask_advisor(
    upload_id: int,
    body: AdvisorQuestionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> AdvisorAnswer:
    upload = await UploadService(db).get_for_user(user.id, upload_id)  # ownership check
    return await advisor_service.answer_question(
        db, upload=upload, question=body.question, language=body.language
    )
