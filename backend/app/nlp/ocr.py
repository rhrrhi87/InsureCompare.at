"""OCR + plain-text extraction.

File: backend/app/nlp/ocr.py

Strategy:
    1. Try direct text extraction with pdfminer.six. If we get >50 tokens we
       assume it's a vector PDF and skip OCR (factor-of-five latency win).
    2. Otherwise rasterise each PDF page (or treat the upload as an image) and
       run Tesseract with the German language pack at PSM 6 (single block).
    3. Compute mean OCR confidence so the application layer can warn users on
       degraded scans.
"""
from __future__ import annotations

import io
import os
import shutil
from dataclasses import dataclass, field

import pdfminer.high_level
import pymupdf
import pytesseract
from PIL import Image

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("nlp.ocr")

# Common Windows install location used by the official UB-Mannheim/tesseract
# installer, which does not reliably add itself to PATH. Checked only as a
# last resort, after settings.TESSERACT_CMD and the normal PATH lookup.
_WINDOWS_FALLBACK_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _configure_tesseract_cmd() -> None:
    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        return
    if shutil.which("tesseract"):
        return  # already resolvable on PATH — nothing to do
    if os.name == "nt" and os.path.isfile(_WINDOWS_FALLBACK_PATH):
        logger.warning(
            "tesseract not on PATH; falling back to default Windows install "
            "location. Set TESSERACT_CMD to silence this.",
            path=_WINDOWS_FALLBACK_PATH,
        )
        pytesseract.pytesseract.tesseract_cmd = _WINDOWS_FALLBACK_PATH


_configure_tesseract_cmd()

# Heuristic: a PDF that yields more than this many whitespace-split tokens is
# treated as a vector PDF and OCR is skipped.
_VECTOR_PDF_TOKEN_THRESHOLD = 50


@dataclass
class OCRResult:
    text: str
    used_ocr: bool
    mean_confidence: float | None = None
    pages: int = 1
    warnings: list[str] = field(default_factory=list)


def _normalise(text: str) -> str:
    """Clean common artefacts from German legal PDFs.

    - Join hyphenated line-breaks (``stra-\\nße`` -> ``straße``)
    - Strip soft hyphens (U+00AD)
    - Replace non-breaking spaces with regular spaces
    """
    return (
        text.replace("\u00ad", "")
        .replace("-\n", "")
        .replace("\xa0", " ")
        .strip()
    )


def _extract_pdf_text(payload: bytes) -> str:
    """Direct text extraction from a vector PDF, no OCR."""
    return pdfminer.high_level.extract_text(io.BytesIO(payload))


def _ocr_image(payload: bytes) -> tuple[str, float]:
    """Run Tesseract on a raster image and return (text, mean_confidence)."""
    image = Image.open(io.BytesIO(payload))
    if image.mode != "RGB":
        image = image.convert("RGB")
    text = pytesseract.image_to_string(
        image, lang=settings.OCR_LANGUAGE, config="--psm 6"
    )
    data = pytesseract.image_to_data(
        image, lang=settings.OCR_LANGUAGE,
        output_type=pytesseract.Output.DICT,
    )
    confidences = [int(c) for c in data.get("conf", []) if c not in ("-1", -1, "")]
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return text, mean_conf


def _rasterise_pdf_pages(payload: bytes) -> list[bytes]:
    """Render every PDF page to a 144-DPI PNG for the OCR fallback.

    Pillow cannot reliably open PDF bytes directly on Windows. The previous
    fallback passed the PDF to ``Image.open`` and therefore failed exactly
    when OCR was required. PyMuPDF is already pinned by the project and gives
    a deterministic, cross-platform rasterisation path.
    """
    pages: list[bytes] = []
    with pymupdf.open(stream=payload, filetype="pdf") as document:
        matrix = pymupdf.Matrix(2.0, 2.0)
        for page in document:
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            pages.append(pixmap.tobytes("png"))
    return pages


def extract_text(payload: bytes, content_type: str) -> OCRResult:
    """Extract text from an arbitrary upload, falling back to OCR.

    Args:
        payload: raw file bytes.
        content_type: MIME type as supplied by the client (validated upstream).

    Returns:
        OCRResult with normalised text and metadata.
    """
    is_pdf = content_type == "application/pdf"
    is_image = content_type in {"image/jpeg", "image/png"}

    if not (is_pdf or is_image):
        raise ValueError(f"Unsupported content type for OCR: {content_type}")

    warnings: list[str] = []

    # ---- 1) Try vector-PDF extraction first ----
    if is_pdf:
        try:
            text = _extract_pdf_text(payload)
        except Exception as exc:                                  # pragma: no cover
            logger.warning("pdfminer extraction failed", error=str(exc))
            text = ""

        token_count = len(text.split())
        if token_count > _VECTOR_PDF_TOKEN_THRESHOLD:
            return OCRResult(
                text=_normalise(text),
                used_ocr=False,
                mean_confidence=None,
                pages=1,
                warnings=warnings,
            )
        warnings.append("Vector text extraction below threshold; falling back to OCR.")

    # ---- 2) OCR ----
    if is_pdf:
        raster_pages = _rasterise_pdf_pages(payload)
        if not raster_pages:
            raise ValueError("PDF contains no renderable pages")
        page_results = [_ocr_image(page) for page in raster_pages]
        text = "\f".join(result[0] for result in page_results)
        conf = sum(result[1] for result in page_results) / len(page_results)
        pages = len(page_results)
    else:
        text, conf = _ocr_image(payload)
        pages = 1

    if conf < settings.OCR_CONFIDENCE_THRESHOLD:
        warnings.append(
            f"Low OCR confidence ({conf:.1f}). The extracted text may contain errors."
        )

    return OCRResult(
        text=_normalise(text),
        used_ocr=True,
        mean_confidence=conf,
        pages=pages,
        warnings=warnings,
    )
