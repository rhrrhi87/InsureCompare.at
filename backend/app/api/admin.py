"""Admin-only endpoints (stats, audit log, user listing).

File: backend/app/api/admin.py
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_only
from app.db.models import User
from app.db.session import get_db
from app.schemas.misc import AdminStats, AuditLogOut, UploadOut
from app.schemas.user import UserOut
from app.services.admin_service import AdminService
from app.services.upload_service import UploadService
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/stats",
    response_model=AdminStats,
    summary="High-level platform KPIs (users, policies, uploads, recommendations)",
)
async def stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
) -> AdminStats:
    return await AdminService(db).stats()


@router.get(
    "/users",
    response_model=list[UserOut],
    summary="List all users (admin only)",
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
) -> list[UserOut]:
    users = await UserService(db).list_all()
    return [UserOut.model_validate(u) for u in users]


@router.get(
    "/audit",
    response_model=list[AuditLogOut],
    summary="Retrieve the audit log",
)
async def list_audit(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AuditLogOut]:
    rows = await AdminService(db).list_audit_log(limit=limit)
    return [AuditLogOut.model_validate(r) for r in rows]


@router.get(
    "/uploads",
    response_model=list[UploadOut],
    summary="Review all user-uploaded documents and their extraction status",
)
async def list_uploads(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[UploadOut]:
    uploads = await AdminService(db).list_uploads(limit=limit)
    return [UploadService.to_out(u) for u in uploads]
