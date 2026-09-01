"""Document upload + extraction endpoints.

File: backend/app/api/documents.py
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.misc import UploadOut
from app.services.admin_service import AdminService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=UploadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a policy document for OCR + NLP extraction",
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> UploadOut:
    payload = await file.read()
    upload = await UploadService(db).ingest(
        user_id=user.id,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        payload=payload,
    )
    await AdminService(db).record_action(
        actor_id=user.id, actor_email=user.email, action="UPLOAD_PROCESSED",
        entity_type="upload", entity_id=upload.id,
        payload={"status": upload.status.value},
    )
    return UploadService.to_out(upload)


@router.get(
    "",
    response_model=list[UploadOut],
    summary="List the current user's uploads",
)
async def list_my_uploads(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> list[UploadOut]:
    items = await UploadService(db).list_for_user(user.id)
    return [UploadService.to_out(u) for u in items]


@router.get(
    "/{upload_id}",
    response_model=UploadOut,
    summary="Retrieve a single upload (status + extracted payload)",
)
async def get_upload(
    upload_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
) -> UploadOut:
    upload = await UploadService(db).get_for_user(user.id, upload_id)
    return UploadService.to_out(upload)
