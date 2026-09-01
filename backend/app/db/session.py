"""SQLAlchemy 2.0 async engine, session factory and FastAPI dependency.

File: backend/app/db/session.py
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# echo=False in production; flip to True locally for SQL debugging.
# pool_size/max_overflow only apply to QueuePool-based dialects (e.g.
# asyncpg); SQLite (used by the test suite, see tests/conftest.py) uses
# StaticPool/NullPool and rejects those kwargs outright.
_engine_kwargs: dict = {"pool_pre_ping": True, "echo": False, "future": True}
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a transactional database session.

    Commits on success and rolls back on any exception. Sessions are always
    closed.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
