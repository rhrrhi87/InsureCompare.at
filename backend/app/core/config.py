"""Application configuration loaded from environment variables.

File: backend/app/core/config.py
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are read from environment variables (or a .env file in development).
    Production deployments should provide secrets through the orchestrator.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Environment ---
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"

    # --- Database ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://app:app@localhost:5432/insurecompare",
        description="Async SQLAlchemy URL (asyncpg driver).",
    )

    # --- Auth ---
    JWT_SECRET: str = Field(
        default="dev-only-change-in-prod",
        min_length=16,
        description="HMAC secret used to sign JWTs.",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_MINUTES: int = 30
    JWT_REFRESH_TOKEN_DAYS: int = 14

    # --- Rate limiting & uploads ---
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # --- CORS ---
    BACKEND_CORS_ORIGINS: str = "https://localhost,http://localhost:5173"

    # --- NLP / OCR ---
    SPACY_MODEL: str = "de_core_news_lg"
    # Must be a model with an NLI/entailment head to work as a zero-shot
    # classifier. "deepset/gbert-base" is a plain pretrained BERT checkpoint
    # with no classification head — HuggingFace's zero-shot-classification
    # pipeline still "loads" it (with a freshly randomly-initialised
    # classifier head) but then every input gets classified into the same
    # class, since the head was never trained. This was verified against a
    # real OCR'd document during manual QA: every clause type came back
    # identical regardless of content. German_Zeroshot is fine-tuned on
    # XNLI specifically for this purpose.
    GBERT_MODEL: str = "Sahajtomar/German_Zeroshot"
    OCR_LANGUAGE: str = "deu"
    OCR_CONFIDENCE_THRESHOLD: int = 70
    # Absolute path to the tesseract binary. Leave unset inside the Docker
    # image (tesseract-ocr is installed to PATH there — see Dockerfile).
    # On native Windows dev installs, the official installer does not
    # reliably add itself to PATH, so pytesseract's default `tesseract_cmd`
    # lookup fails with "tesseract is not installed or it's not in your
    # PATH" even though it is installed — set this explicitly in that case.
    TESSERACT_CMD: str | None = None

    # --- AI Policy Advisor (LLM) ---
    # "gemini" for the real Google Gemini API, "mock" for a deterministic
    # in-process provider used by tests/CI so they never make live API
    # calls. See docs/AI_ADVISOR_ARCHITECTURE.md.
    LLM_PROVIDER: Literal["gemini", "mock"] = "mock"
    GEMINI_API_KEY: str | None = None
    # gemini-3.6-flash: current Flash model available to new Gemini API users.
    # The earlier gemini-2.5-flash identifier now returns 404 for new users.
    GEMINI_MODEL: str = "gemini-3.6-flash"
    GEMINI_MAX_OUTPUT_TOKENS: int = 1024
    GEMINI_TIMEOUT_SECONDS: int = 20

    # --- Demo seed accounts ---
    SEED_DEMO_USER_EMAIL: str = "user@test.at"
    SEED_DEMO_USER_PASSWORD: str = "user123"
    SEED_DEMO_ADMIN_EMAIL: str = "admin@insurance.at"
    SEED_DEMO_ADMIN_PASSWORD: str = "admin123"

    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def split_cors(cls, value: str) -> str:
        """Allow comma-separated origin lists; stored as a single string."""
        return value.strip()

    @property
    def cors_origins(self) -> list[str]:
        """Origins as a Python list for FastAPI CORSMiddleware."""
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor used as a FastAPI dependency."""
    return Settings()


settings = get_settings()
