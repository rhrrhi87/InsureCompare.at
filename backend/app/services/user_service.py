"""User application service: registration, authentication, retrieval.

File: backend/app/services/user_service.py
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnauthorisedError
from app.core.security import hash_password, verify_password
from app.db.enums import UserRole
from app.db.models import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Domain logic for the User aggregate."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---- Reads ----
    async def get_by_id(self, user_id: int) -> User:
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[User]:
        result = await self.db.execute(select(User).order_by(User.id))
        return list(result.scalars().all())

    # ---- Writes ----
    async def register(self, payload: UserCreate, role: UserRole = UserRole.USER) -> User:
        existing = await self.get_by_email(payload.email)
        if existing:
            raise ConflictError("A user with this email already exists")

        user = User(
            email=payload.email.lower(),
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            role=role,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorisedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorisedError("User account is inactive")
        return user

    async def update(self, user_id: int, payload: UserUpdate) -> User:
        user = await self.get_by_id(user_id)
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.password is not None:
            user.password_hash = hash_password(payload.password)
        await self.db.flush()
        await self.db.refresh(user)
        return user
