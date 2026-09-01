"""Pytest fixtures for backend tests.

File: backend/tests/conftest.py

Uses an in-memory SQLite database (aiosqlite) for fast unit / integration tests
without requiring Postgres. The Alembic migration is bypassed and tables are
created directly from SQLAlchemy metadata.
"""
from __future__ import annotations

import os
from collections.abc import AsyncIterator

# Force test environment BEFORE importing application code.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-1234567890")
# Unit/integration tests must never inherit the developer's live Gemini
# configuration or make paid/external API calls.
os.environ.setdefault("LLM_PROVIDER", "mock")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.db.enums import (
    CoverageLevel,
    DeductiblePreference,
    ProductLine,
    RiskTolerance,
    UserRole,
)
from app.db.models import Policy, Provider, RiskProfile, User
from app.db.session import get_db
from app.main import app as fastapi_app


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def seeded_db(db_session: AsyncSession) -> AsyncSession:
    """Seed a couple of providers, policies and a demo user."""
    uniqa = Provider(name="UNIQA", country="AT", rating_score=8.6)
    allianz = Provider(name="Allianz Austria", country="AT", rating_score=8.8)
    db_session.add_all([uniqa, allianz])
    await db_session.flush()

    db_session.add_all([
        Policy(
            provider_id=uniqa.id, name="UNIQA Kfz Premium",
            product_line=ProductLine.CAR,
            monthly_premium_eur=70.0, annual_premium_eur=840.0,
            deductible_eur=500.0, coverage_limit_eur=100_000_000.0,
            coverage_items=[
                "Liability coverage", "Comprehensive coverage", "Collision coverage",
                "Glass breakage", "Theft protection",
            ],
            additional_features=["24/7 Roadside assistance"],
            exclusions=["Racing events", "Intentional damage"],
        ),
        Policy(
            provider_id=allianz.id, name="Allianz Auto Komplett",
            product_line=ProductLine.CAR,
            monthly_premium_eur=76.67, annual_premium_eur=920.0,
            deductible_eur=300.0, coverage_limit_eur=150_000_000.0,
            coverage_items=[
                "Liability coverage", "Comprehensive coverage", "Collision coverage",
                "Glass breakage", "Theft protection", "Personal accident",
            ],
            additional_features=["Roadside assistance"],
            exclusions=["Racing events"],
        ),
    ])

    user = User(
        email="user@test.at",
        full_name="Test User",
        password_hash=hash_password("user123"),
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(RiskProfile(
        user_id=user.id,
        insurance_type=ProductLine.CAR,
        monthly_budget_eur=100.0,
        risk_tolerance=RiskTolerance.MEDIUM,
        coverage_level=CoverageLevel.STANDARD,
        deductible_preference=DeductiblePreference.MEDIUM,
        household_size=1,
        required_coverages=[],
        weights={},
    ))

    db_session.add(User(
        email="admin@insurance.at",
        full_name="Admin User",
        password_hash=hash_password("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
    ))
    await db_session.commit()
    return db_session


@pytest_asyncio.fixture
async def client(seeded_db: AsyncSession) -> AsyncIterator[AsyncClient]:
    """An HTTPX async client wired into the FastAPI app, sharing the test DB."""

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield seeded_db

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()
