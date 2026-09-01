"""FastAPI router modules."""
from app.api import (
    admin,
    auth,
    compare,
    documents,
    health,
    policies,
    profiles,
    recommendations,
)

__all__ = [
    "admin",
    "auth",
    "compare",
    "documents",
    "health",
    "policies",
    "profiles",
    "recommendations",
]
