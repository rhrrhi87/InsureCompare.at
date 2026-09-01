"""Pydantic schemas re-exported from one module for ergonomic imports."""
from app.schemas.common import MessageResponse, Page, RefreshRequest, TokenResponse
from app.schemas.misc import (
    AdminStats,
    AuditLogOut,
    CompareRequest,
    CompareResponse,
    CompareSummary,
    ExtractedClauseOut,
    ExtractedDocument,
    UploadOut,
)
from app.schemas.policy import (
    PolicyCreate,
    PolicyOut,
    PolicyUpdate,
    ProviderCreate,
    ProviderOut,
    ProviderUpdate,
)
from app.schemas.profile import RiskProfileOut, RiskProfileUpdate, WeightConfig
from app.schemas.recommendation import (
    FeatureContribution,
    RecommendationRequest,
    RecommendationResponse,
    ScoredPolicy,
)
from app.schemas.user import UserCreate, UserLogin, UserOut, UserUpdate

__all__ = [
    # common
    "MessageResponse", "Page", "RefreshRequest", "TokenResponse",
    # user
    "UserCreate", "UserLogin", "UserOut", "UserUpdate",
    # profile
    "RiskProfileOut", "RiskProfileUpdate", "WeightConfig",
    # policy / provider
    "PolicyCreate", "PolicyOut", "PolicyUpdate",
    "ProviderCreate", "ProviderOut", "ProviderUpdate",
    # recommendation
    "FeatureContribution", "RecommendationRequest", "RecommendationResponse", "ScoredPolicy",
    # misc
    "AdminStats", "AuditLogOut",
    "CompareRequest", "CompareResponse", "CompareSummary",
    "ExtractedClauseOut", "ExtractedDocument", "UploadOut",
]
