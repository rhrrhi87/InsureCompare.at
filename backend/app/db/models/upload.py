"""User-uploaded policy documents (raw + processing status).

File: backend/app/db/models/upload.py
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, str_enum
from app.db.enums import UploadStatus

if TYPE_CHECKING:
    from app.db.models.user import User


class Upload(Base, TimestampMixin):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Object-storage key OR base64 hash (academic prototype keeps SHA-256).
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    status: Mapped[UploadStatus] = mapped_column(
        str_enum(UploadStatus, name="upload_status"),
        default=UploadStatus.QUEUED,
        nullable=False,
        index=True,
    )

    # OCR confidence 0-100 (mean character confidence reported by Tesseract).
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))

    # Final extracted structured payload (clauses, premium, deductible, …)
    extracted: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Cached AI Policy Advisor summary (see app/services/advisor_service.py).
    # Kept separate from `extracted` (which has a strict Pydantic shape) so
    # the Advisor's LLM-generated overview is never confused with, or
    # accidentally validated against, the deterministic NLP extraction
    # result. Shape: {"language": "de"|"en", "summary": {...}, "evidence": [...]}.
    advisor_summary: Mapped[dict | None] = mapped_column(JSON)

    user: Mapped[User] = relationship(back_populates="uploads")

    def __repr__(self) -> str:
        return (
            f"<Upload id={self.id} user={self.user_id} "
            f"filename={self.filename!r} status={self.status.value}>"
        )
