"""Enumerations used throughout the data model.

File: backend/app/db/enums.py
"""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class ProductLine(str, enum.Enum):
    """In-scope retail insurance product lines."""

    CAR = "car"
    HOUSEHOLD = "household"
    TRAVEL = "travel"
    LEGAL = "legal"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskTolerance(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CoverageLevel(str, enum.Enum):
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class DeductiblePreference(str, enum.Enum):
    LOW = "low"        # €150-300
    MEDIUM = "medium"  # €400-600
    HIGH = "high"      # €700-1000


class UploadStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ClauseType(str, enum.Enum):
    COVERAGE = "coverage"
    EXCLUSION = "exclusion"
    LIMIT = "limit"
    DEDUCTIBLE = "deductible"
    OBLIGATION = "obligation"
    DEFINITION = "definition"
    TERRITORIAL_SCOPE = "territorial_scope"
    DURATION = "duration"
    OPTIONAL_BENEFIT = "optional_benefit"
    OTHER = "other"


class ExtractionMethod(str, enum.Enum):
    """How a clause's structured data reached the database."""

    SEED = "seed"
    OCR_NLP = "ocr_nlp"
    MANUAL = "manual"
