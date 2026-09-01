"""SQLAlchemy ORM models for InsureCompare.at.

File: backend/app/db/models/__init__.py

Imported here so that ``Base.metadata`` is fully populated when Alembic
auto-generates migrations.
"""
from app.db.models.policy import Clause, Policy
from app.db.models.profile import RiskProfile
from app.db.models.provider import Provider
from app.db.models.recommendation import AuditLog, Recommendation
from app.db.models.session import Session
from app.db.models.upload import Upload
from app.db.models.user import User

__all__ = [
    "AuditLog",
    "Clause",
    "Policy",
    "Provider",
    "Recommendation",
    "RiskProfile",
    "Session",
    "Upload",
    "User",
]
