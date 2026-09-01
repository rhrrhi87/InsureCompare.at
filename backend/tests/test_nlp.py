"""Unit tests for the German clause extractor (deterministic fallback path).

File: backend/tests/test_nlp.py
"""
from __future__ import annotations

import pytest

from app.db.enums import ClauseType
from app.nlp import ocr
from app.nlp.extractor import ClauseExtractor


@pytest.fixture
def extractor() -> ClauseExtractor:
    """Force the keyword fallback so tests are deterministic and fast."""
    inst = ClauseExtractor()
    inst._spacy = False  # type: ignore[assignment]
    inst._classifier = False  # type: ignore[assignment]
    return inst


def test_extracts_monthly_premium(extractor: ClauseExtractor) -> None:
    text = "Die monatliche Prämie beträgt € 70,00 pro Monat."
    result = extractor.extract(text)
    assert result.monthly_premium_eur == pytest.approx(70.0)


def test_extracts_deductible(extractor: ClauseExtractor) -> None:
    text = "Der Selbstbehalt beträgt € 500,00 pro Schadenfall."
    result = extractor.extract(text)
    assert result.deductible_eur == pytest.approx(500.0)


def test_extracts_coverage_limit_with_german_thousands(extractor: ClauseExtractor) -> None:
    text = "Die Versicherungssumme beträgt € 1.234.567,89 maximal."
    result = extractor.extract(text)
    assert result.coverage_limit_eur == pytest.approx(1_234_567.89)


def test_classifies_exclusion_clause(extractor: ClauseExtractor) -> None:
    text = (
        "Die Haftung erstreckt sich auf Schäden durch Brand. "
        "Schäden durch grobe Fahrlässigkeit sind ausgeschlossen."
    )
    result = extractor.extract(text)
    types = {c.clause_type for c in result.clauses}
    assert ClauseType.EXCLUSION in types


def test_detects_coverage_vocabulary(extractor: ClauseExtractor) -> None:
    text = "Versichert sind Diebstahl, Sturm und Glasbruch im Haushalt."
    result = extractor.extract(text)
    assert "Theft protection" in result.coverages
    assert "Storm damage" in result.coverages
    assert "Glass breakage" in result.coverages


def test_short_sentences_are_ignored(extractor: ClauseExtractor) -> None:
    result = extractor.extract("Hi. Bye.")
    assert result.clauses == []


def test_classifies_deductible_clause(extractor: ClauseExtractor) -> None:
    text = (
        "Die Versicherung ersetzt Schäden am Fahrzeug nach einem Unfall. "
        "Der Selbstbehalt beträgt in jedem Schadenfall EUR 300."
    )
    result = extractor.extract(text)
    types = {c.clause_type for c in result.clauses}
    assert ClauseType.DEDUCTIBLE in types


def test_classifies_territorial_scope_clause(extractor: ClauseExtractor) -> None:
    text = (
        "Die Versicherung bietet umfassenden Schutz für Ihr Fahrzeug. "
        "Der Geltungsbereich dieser Police umfasst alle Länder Europas."
    )
    result = extractor.extract(text)
    types = {c.clause_type for c in result.clauses}
    assert ClauseType.TERRITORIAL_SCOPE in types


def test_clause_page_numbers_follow_form_feed_boundaries(
    extractor: ClauseExtractor,
) -> None:
    text = (
        "Versichert sind Schäden durch Feuer und Sturm am Gebäude.\f"
        "Nicht versichert sind Schäden durch Kernenergie und Krieg."
    )
    result = extractor.extract(text)
    assert [clause.page_number for clause in result.clauses] == [1, 2]


def test_vector_pdf_with_sufficient_text_skips_ocr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = " ".join(["Versicherungsinformation"] * 51)
    monkeypatch.setattr(ocr, "_extract_pdf_text", lambda payload: text)
    monkeypatch.setattr(
        ocr,
        "_rasterise_pdf_pages",
        lambda payload: pytest.fail("rasterisation should not run"),
    )

    result = ocr.extract_text(b"vector-pdf", "application/pdf")

    assert result.used_ocr is False
    assert result.text == text


def test_pdf_below_threshold_rasterises_and_ocrs_every_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ocr, "_extract_pdf_text", lambda payload: "")
    monkeypatch.setattr(
        ocr, "_rasterise_pdf_pages", lambda payload: [b"page-one", b"page-two"]
    )

    def fake_ocr(payload: bytes) -> tuple[str, float]:
        return (
            ("Erste Seite", 90.0)
            if payload == b"page-one"
            else ("Zweite Seite", 80.0)
        )

    monkeypatch.setattr(ocr, "_ocr_image", fake_ocr)

    result = ocr.extract_text(b"scanned-pdf", "application/pdf")

    assert result.used_ocr is True
    assert result.pages == 2
    assert result.mean_confidence == pytest.approx(85.0)
    assert result.text == "Erste Seite\fZweite Seite"
