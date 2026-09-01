"""FastAPI dependencies: extract the current user from a bearer JWT.

File: backend/app/api/deps.py
"""
from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorisedError, domain_to_http
from app.core.security import decode_token
from app.db.enums import UserRole
from app.db.models import User
from app.db.session import get_db
from app.services.user_service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


async def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise domain_to_http(UnauthorisedError("Missing or invalid Authorization header"))

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except UnauthorisedError as exc:
        raise domain_to_http(exc) from exc

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise domain_to_http(UnauthorisedError("Invalid token subject")) from exc

    service = UserService(db)
    try:
        user = await service.get_by_id(user_id)
    except Exception as exc:
        raise domain_to_http(UnauthorisedError("User not found")) from exc

    if not user.is_active:
        raise domain_to_http(UnauthorisedError("Inactive user"))

    # Make the user available to downstream middleware (e.g. audit logger).
    request.state.user_id = user.id
    request.state.user_email = user.email
    request.state.user_role = user.role.value
    return user


async def admin_only(user: User = Depends(current_user)) -> User:
    if user.role is not UserRole.ADMIN:
        raise domain_to_http(ForbiddenError("Admin privileges required"))
    return user
