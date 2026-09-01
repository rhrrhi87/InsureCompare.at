"""Upload service.

File: backend/app/services/upload_service.py

Persists user uploads, runs the OCR + NLP pipeline (synchronously for the
prototype; in production this would be enqueued onto a worker like RQ /
Celery / Arq), and writes the structured extraction back onto the upload
row.
"""
from __future__ import annotations

import asyncio
import hashlib
from typing import Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    NotFoundError,
    UnsupportedMediaError,
    UploadTooLargeError,
)
from app.core.logging import get_logger
from app.db.enums import ExtractionMethod, UploadStatus
from app.db.models import Clause, Upload
from app.nlp import clause_extractor, extract_text
from app.schemas.misc import (
    ExtractedClauseOut,
    ExtractedDocument,
    UploadOut,
)

logger = get_logger("services.upload")

ALLOWED_CONTENT_TYPES: Final[set[str]] = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


def _extract_document(payload: bytes, content_type: str):
    """Run CPU-bound OCR/NLP outside FastAPI's asynchronous event loop."""
    ocr = extract_text(payload, content_type)
    extraction = clause_extractor.extract(ocr.text)
    return ocr, extraction


class UploadService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ---- Reads ----
    async def list_for_user(self, user_id: int, limit: int = 25) -> list[Upload]:
        stmt = (
            select(Upload)
            .where(Upload.user_id == user_id)
            .order_by(Upload.created_at.desc())
            .limit(limit)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_for_user(self, user_id: int, upload_id: int) -> Upload:
        stmt = select(Upload).where(
            Upload.id == upload_id, Upload.user_id == user_id
        )
        upload = (await self.db.execute(stmt)).scalar_one_or_none()
        if not upload:
            raise NotFoundError("Upload not found")
        return upload

    # ---- Writes ----
    async def ingest(
        self,
        user_id: int,
        filename: str,
        content_type: str,
        payload: bytes,
    ) -> Upload:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise UnsupportedMediaError(
                f"Unsupported content type '{content_type}'. "
                f"Allowed: {sorted(ALLOWED_CONTENT_TYPES)}."
            )
        if len(payload) > settings.MAX_UPLOAD_BYTES:
            raise UploadTooLargeError(
                f"File too large ({len(payload)} bytes). "
                f"Maximum allowed: {settings.MAX_UPLOAD_BYTES} bytes."
            )

        digest = hashlib.sha256(payload).hexdigest()

        upload = Upload(
            user_id=user_id,
            filename=filename[:255],
            content_type=content_type,
            size_bytes=len(payload),
            storage_key=f"uploads/{user_id}/{digest}",
            sha256=digest,
            status=UploadStatus.PROCESSING,
        )
        self.db.add(upload)
        await self.db.flush()
        await self.db.refresh(upload)

        # ---- Run extraction pipeline ----
        try:
            ocr, extraction = await asyncio.to_thread(
                _extract_document, payload, content_type
            )

            extracted_payload = ExtractedDocument(
                monthly_premium_eur=extraction.monthly_premium_eur,
                annual_premium_eur=extraction.annual_premium_eur,
                deductible_eur=extraction.deductible_eur,
                coverage_limit_eur=extraction.coverage_limit_eur,
                coverages=extraction.coverages,
                exclusions=extraction.exclusions,
                clauses=[
                    ExtractedClauseOut(
                        clause_type=c.clause_type,
                        label=c.label,
                        text=c.text[:1000],
                        confidence=round(c.confidence, 3),
                        page_number=c.page_number,
                    )
                    for c in extraction.clauses[:200]
                ],
                raw_text_excerpt=ocr.text[:2000],
            ).model_dump(mode="json")

            upload.extracted = extracted_payload
            upload.ocr_confidence = ocr.mean_confidence
            upload.status = UploadStatus.READY
            if ocr.warnings:
                upload.error_message = " | ".join(ocr.warnings)

            # Persist canonical Clause rows alongside the denormalised JSON
            # summary above, so the evidence viewer can query real clauses
            # instead of re-parsing the upload's JSON blob.
            for clause in extraction.clauses[:200]:
                self.db.add(
                    Clause(
                        policy_id=None,
                        upload_id=upload.id,
                        clause_type=clause.clause_type,
                        label=clause.label,
                        text=clause.text[:1000],
                        document_language="de",
                        page_number=clause.page_number,
                        confidence=round(clause.confidence, 3),
                        extraction_method=ExtractionMethod.OCR_NLP,
                    )
                )

            logger.info(
                "Extraction complete",
                upload_id=upload.id,
                used_ocr=ocr.used_ocr,
                clauses=len(extraction.clauses),
            )
        except Exception as exc:                                  # pragma: no cover
            logger.exception("Extraction failed", upload_id=upload.id)
            upload.status = UploadStatus.FAILED
            upload.error_message = str(exc)[:1000]

        await self.db.flush()
        await self.db.refresh(upload)
        return upload

    @staticmethod
    def to_out(upload: Upload) -> UploadOut:
        extracted = (
            ExtractedDocument.model_validate(upload.extracted) if upload.extracted else None
        )
        return UploadOut(
            id=upload.id,
            user_id=upload.user_id,
            filename=upload.filename,
            content_type=upload.content_type,
            size_bytes=upload.size_bytes,
            status=upload.status,
            ocr_confidence=float(upload.ocr_confidence) if upload.ocr_confidence else None,
            extracted=extracted,
            error_message=upload.error_message,
            created_at=upload.created_at,
        )
