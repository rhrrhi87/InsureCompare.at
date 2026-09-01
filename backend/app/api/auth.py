"""Authentication endpoints.

File: backend/app/api/auth.py
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.core.config import settings
from app.core.exceptions import UnauthorisedError, domain_to_http
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.db.models import User
from app.db.session import get_db
from app.schemas.common import MessageResponse, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.services.admin_service import AdminService
from app.services.session_service import SessionService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id), user.role.value)
    await SessionService(db).create(user.id, refresh)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_MINUTES * 60,
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    try:
        user = await UserService(db).register(payload)
    except Exception:                                      # pragma: no cover
        # ConflictError -> 409 etc. handled centrally in main.py
        raise
    return UserOut.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Exchange credentials for an access + refresh token pair",
)
async def login(
    payload: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await UserService(db).authenticate(payload.email, payload.password)
    tokens = await _issue_tokens(db, user)
    await AdminService(db).record_action(
        actor_id=user.id, actor_email=user.email, action="LOGIN",
        entity_type="user", entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new access + refresh pair (rotates the session)",
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
    except UnauthorisedError as exc:
        raise domain_to_http(exc) from exc

    try:
        session = await SessionService(db).get_active(payload.refresh_token)
    except UnauthorisedError as exc:
        raise domain_to_http(exc) from exc

    user_id = int(token_payload["sub"])
    user = await UserService(db).get_by_id(user_id)
    if not user.is_active:
        raise domain_to_http(UnauthorisedError("Inactive user"))

    # Rotate: the presented refresh token is single-use.
    await SessionService(db).revoke(session)
    return await _issue_tokens(db, user)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke the current refresh token's session",
)
async def logout(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await SessionService(db).revoke_by_token(payload.refresh_token)
    return MessageResponse(message="Logged out")


@router.get(
    "/me",
    response_model=UserOut,
    summary="Return the currently authenticated user",
)
async def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.model_validate(user)
