"""German clause extraction.

File: backend/app/nlp/extractor.py

Two-stage extraction strategy:

1. **Rule-based numeric extraction** for premium / deductible / coverage limit.
   Robust patterns work where transformers do not, and these fields appear in
   nearly every IPID and AVB.
2. **Sentence classification** into COVERAGE / EXCLUSION / LIMIT / DEFINITION /
   OTHER. The pipeline tries to load a domain-adapted gBERT zero-shot
   classifier on first use; if the model is unavailable (offline build, slim
   container) we fall back to a deterministic keyword classifier so the
   pipeline still runs end-to-end.

Both modes share the same public surface (``ClauseExtractor.extract``) so the
rest of the application doesn't care which is in use.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.logging import get_logger
from app.db.enums import ClauseType

logger = get_logger("nlp.extractor")


# ---------------------------------------------------------------------------
# Numeric patterns
# ---------------------------------------------------------------------------
_EUR_AMOUNT = r"(?:€\s?|EUR\s?)([\d\.\,]+)"
_PREMIUM_PATTERN = re.compile(
    rf"(?:monatlich|pro\s+Monat|monatsbeitrag|monatsprämie)[^€\d]{{0,40}}{_EUR_AMOUNT}",
    flags=re.IGNORECASE,
)
_ANNUAL_PATTERN = re.compile(
    rf"(?:jährlich|pro\s+Jahr|jahresbeitrag|jahresprämie)[^€\d]{{0,40}}{_EUR_AMOUNT}",
    flags=re.IGNORECASE,
)
_DEDUCTIBLE_PATTERN = re.compile(
    rf"(?:selbstbehalt|selbstbeteiligung|deductible)[^€\d]{{0,40}}{_EUR_AMOUNT}",
    flags=re.IGNORECASE,
)
_COVERAGE_LIMIT_PATTERN = re.compile(
    rf"(?:versicherungssumme|deckungssumme|haftungsumme|maximalbetrag)[^€\d]{{0,40}}{_EUR_AMOUNT}",
    flags=re.IGNORECASE,
)


def _eur_to_float(raw: str) -> float | None:
    """Parse a German-formatted euro amount (``1.234,56``) to a float."""
    s = raw.strip()
    # German thousands separator . / decimal ,
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Keyword-based clause classifier (fallback for deterministic environments)
# ---------------------------------------------------------------------------
_COVERAGE_KEYWORDS = (
    "versichert", "umfasst", "deckung", "leistung", "schutz", "abgedeckt",
    "übernimmt", "ersetzt", "haftpflicht",
)
_EXCLUSION_KEYWORDS = (
    "nicht versichert", "ausgeschlossen", "keine deckung", "ausschluss",
    "nicht ersetzt", "ausgenommen", "kein versicherungsschutz",
)
_LIMIT_KEYWORDS = (
    "höchstens", "maximal", "bis zu", "maximaler", "begrenzt", "limit",
    "versicherungssumme", "deckungssumme",
)
_DEDUCTIBLE_KEYWORDS = ("selbstbehalt", "selbstbeteiligung")
_OBLIGATION_KEYWORDS = (
    "ist verpflichtet", "hat unverzüglich", "obliegenheit", "muss anzeigen",
    "meldepflicht", "anzeigepflicht",
)
_DEFINITION_KEYWORDS = ("im sinne dieser", "gilt als", "definition", "bedeutet")
_TERRITORIAL_SCOPE_KEYWORDS = (
    "geltungsbereich", "gilt in", "gültigkeitsbereich", "weltweit", "europaweit",
    "innerhalb europas",
)
_DURATION_KEYWORDS = (
    "laufzeit", "vertragsdauer", "vertragsbeginn", "vertragsende", "beginnt am", "endet am",
)
_OPTIONAL_BENEFIT_KEYWORDS = (
    "wahlleistung", "optional", "zusatzbaustein", "gegen mehrprämie", "zubuchbar",
)


def _keyword_classify(sentence: str) -> ClauseType:
    s = sentence.lower()
    for kw in _EXCLUSION_KEYWORDS:
        if kw in s:
            return ClauseType.EXCLUSION
    for kw in _DEDUCTIBLE_KEYWORDS:
        if kw in s:
            return ClauseType.DEDUCTIBLE
    for kw in _LIMIT_KEYWORDS:
        if kw in s:
            return ClauseType.LIMIT
    for kw in _TERRITORIAL_SCOPE_KEYWORDS:
        if kw in s:
            return ClauseType.TERRITORIAL_SCOPE
    for kw in _DURATION_KEYWORDS:
        if kw in s:
            return ClauseType.DURATION
    for kw in _OPTIONAL_BENEFIT_KEYWORDS:
        if kw in s:
            return ClauseType.OPTIONAL_BENEFIT
    for kw in _OBLIGATION_KEYWORDS:
        if kw in s:
            return ClauseType.OBLIGATION
    for kw in _COVERAGE_KEYWORDS:
        if kw in s:
            return ClauseType.COVERAGE
    for kw in _DEFINITION_KEYWORDS:
        if kw in s:
            return ClauseType.DEFINITION
    return ClauseType.OTHER


# ---------------------------------------------------------------------------
# Coverage controlled vocabulary (German -> normalised English label)
# ---------------------------------------------------------------------------
_COVERAGE_VOCAB: dict[str, str] = {
    "haftpflicht": "Liability coverage",
    "vollkasko": "Comprehensive coverage",
    "teilkasko": "Partial comprehensive coverage",
    "kollision": "Collision coverage",
    "glasbruch": "Glass breakage",
    "diebstahl": "Theft protection",
    "feuer": "Fire damage",
    "sturm": "Storm damage",
    "wasser": "Water damage",
    "fahrrad": "Bicycle theft",
    "elektronik": "Home electronics",
    "rechtsschutz": "Legal protection",
    "reisegepäck": "Travel luggage",
    "stornokosten": "Trip cancellation",
    "auslandskrank": "Travel medical",
}

_EXCLUSION_VOCAB: dict[str, str] = {
    "grobe fahrlässigkeit": "Gross negligence",
    "vorsatz": "Intentional damage",
    "rennveranstaltung": "Racing events",
    "kriegerische ereignisse": "War / civil unrest",
    "kernenergie": "Nuclear events",
    "rechtswidrig": "Unlawful actions",
    "alkohol": "Alcohol-related incidents",
    "drogen": "Drug-related incidents",
}


# ---------------------------------------------------------------------------
# Sentence splitting (lightweight, regex-based; spaCy used if available)
# ---------------------------------------------------------------------------
def _split_sentences_simple(text: str) -> list[str]:
    """Regex-based sentence splitter that is robust to German abbreviations."""
    # Protect a small set of common German abbreviations from being split.
    protected = text
    for abbrev in ("z.B.", "z. B.", "bzw.", "ggf.", "lt.", "Nr.", "Art."):
        protected = protected.replace(abbrev, abbrev.replace(".", "§§§DOT§§§"))
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ])", protected)
    return [p.replace("§§§DOT§§§", ".").strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------
@dataclass
class ExtractedClause:
    clause_type: ClauseType
    text: str
    label: str | None = None
    confidence: float = 1.0
    page_number: int | None = None


@dataclass
class ExtractionResult:
    monthly_premium_eur: float | None = None
    annual_premium_eur: float | None = None
    deductible_eur: float | None = None
    coverage_limit_eur: float | None = None
    coverages: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    clauses: list[ExtractedClause] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ClauseExtractor
# ---------------------------------------------------------------------------
class ClauseExtractor:
    """Extracts structured information from a normalised German policy text.

    The class loads heavy dependencies (spaCy, transformers) lazily so that
    importing this module never triggers a network download.
    """

    def __init__(self) -> None:
        self._spacy = None  # type: ignore[var-annotated]
        self._classifier = None  # type: ignore[var-annotated]

    # ----- Lazy loaders -----
    def _get_spacy(self):
        if self._spacy is not None:
            return self._spacy
        try:                                                     # pragma: no cover
            import spacy
            self._spacy = spacy.load(settings.SPACY_MODEL)
            logger.info("spaCy model loaded", model=settings.SPACY_MODEL)
        except Exception as exc:                                 # pragma: no cover
            logger.warning("spaCy unavailable; falling back to regex split", error=str(exc))
            self._spacy = False
        return self._spacy

    def _get_classifier(self):
        if self._classifier is not None:
            return self._classifier
        try:                                                     # pragma: no cover
            from transformers import pipeline as hf_pipeline
            self._classifier = hf_pipeline(
                "zero-shot-classification",
                model=settings.GBERT_MODEL,
                device=-1,  # CPU
                # Request-time document ingestion must never initiate a model
                # download or sit through remote retry backoff. Deployments
                # pre-provision the configured model; if it is not in the
                # local cache, the deterministic keyword path is used.
                model_kwargs={"local_files_only": True},
            )
            logger.info("gBERT classifier loaded", model=settings.GBERT_MODEL)
        except Exception as exc:                                 # pragma: no cover
            logger.warning(
                "gBERT classifier unavailable; using keyword fallback", error=str(exc)
            )
            self._classifier = False
        return self._classifier

    # ----- Internals -----
    def _split_sentences(self, text: str) -> list[str]:
        nlp = self._get_spacy()
        if nlp:                                                  # pragma: no cover
            return [s.text.strip() for s in nlp(text).sents if s.text.strip()]
        return _split_sentences_simple(text)

    def _classify(self, sentence: str) -> tuple[ClauseType, float]:
        clf = self._get_classifier()
        if not clf:                                              # offline path
            return _keyword_classify(sentence), 0.7
        try:                                                     # pragma: no cover
            result = clf(
                sentence,
                candidate_labels=[c.value for c in ClauseType],
                multi_label=False,
            )
            label = ClauseType(result["labels"][0])
            return label, float(result["scores"][0])
        except Exception:                                        # pragma: no cover
            return _keyword_classify(sentence), 0.6

    @staticmethod
    def _match_first_amount(text: str, pattern: re.Pattern[str]) -> float | None:
        for match in pattern.finditer(text):
            value = _eur_to_float(match.group(1))
            if value is not None:
                return value
        return None

    @staticmethod
    def _scan_vocab(text: str, vocab: dict[str, str]) -> list[str]:
        lower = text.lower()
        return sorted({label for needle, label in vocab.items() if needle in lower})

    # ----- Public API -----
    def extract(self, text: str) -> ExtractionResult:
        """Run the full extraction pipeline on already-OCR'd text."""
        result = ExtractionResult(
            monthly_premium_eur=self._match_first_amount(text, _PREMIUM_PATTERN),
            annual_premium_eur=self._match_first_amount(text, _ANNUAL_PATTERN),
            deductible_eur=self._match_first_amount(text, _DEDUCTIBLE_PATTERN),
            coverage_limit_eur=self._match_first_amount(text, _COVERAGE_LIMIT_PATTERN),
            coverages=self._scan_vocab(text, _COVERAGE_VOCAB),
            exclusions=self._scan_vocab(text, _EXCLUSION_VOCAB),
        )

        # pdfminer and the OCR fallback both use form-feed characters as
        # page boundaries. Classifying one page at a time preserves a real
        # page number on each stored clause for later evidence display.
        pages = [page.strip() for page in re.split(r"\f+", text) if page.strip()]
        if not pages:
            pages = [text]
        for page_number, page_text in enumerate(pages, start=1):
            sentences = self._split_sentences(page_text)
            for sentence in self._iter_meaningful(sentences):
                clause_type, confidence = self._classify(sentence)
                if clause_type is ClauseType.OTHER:
                    continue
                result.clauses.append(
                    ExtractedClause(
                        clause_type=clause_type,
                        text=sentence,
                        confidence=confidence,
                        page_number=page_number,
                    )
                )
        return result

    @staticmethod
    def _iter_meaningful(sentences: Iterable[str]) -> Iterable[str]:
        """Filter out very short or boiler-plate sentences."""
        for s in sentences:
            stripped = s.strip()
            if len(stripped.split()) < 4:
                continue
            yield stripped


# Singleton used by the upload service.
clause_extractor = ClauseExtractor()
