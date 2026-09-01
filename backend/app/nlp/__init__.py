"""Natural language processing pipeline for InsureCompare.at."""
from app.nlp.extractor import ClauseExtractor, ExtractionResult, clause_extractor
from app.nlp.ocr import OCRResult, extract_text

__all__ = [
    "ClauseExtractor",
    "ExtractionResult",
    "OCRResult",
    "clause_extractor",
    "extract_text",
]
