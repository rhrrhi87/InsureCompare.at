"""Authentication primitives: password hashing and JWT issuance / verification.

File: backend/app/core/security.py
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorisedError

# bcrypt with a sensible cost factor; passlib handles salt management.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

TokenType = Literal["access", "refresh"]


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison of plaintext against bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


def _create_token(
    subject: str,
    token_type: TokenType,
    role: str,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    """Build and sign a JWT.

    Includes a random ``jti`` so two tokens issued for the same subject in
    the same second (e.g. rapid refresh-rotation) are never byte-identical
    — identical tokens would hash to the same value in ``sessions`` and
    silently defeat single-use rotation.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str, role: str) -> str:
    """Short-lived JWT used to authorise API calls."""
    return _create_token(
        subject=subject,
        token_type="access",
        role=role,
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_MINUTES),
    )


def create_refresh_token(subject: str, role: str) -> str:
    """Long-lived JWT used to obtain new access tokens."""
    return _create_token(
        subject=subject,
        token_type="refresh",
        role=role,
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_DAYS),
    )


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    """Validate signature, expiry and (optionally) the token type.

    Raises ``UnauthorisedError`` for any verification failure.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise UnauthorisedError("Invalid or expired token") from exc

    if expected_type and payload.get("type") != expected_type:
        raise UnauthorisedError("Wrong token type")
    if not payload.get("sub"):
        raise UnauthorisedError("Token missing subject")
    return payload


def hash_token(token: str) -> str:
    """SHA-256 hex digest used to store/verify a refresh token server-side
    without ever persisting the bearer token itself."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
