# Document Processing / OCR / NLP Pipeline

## Pipeline stages

```
Upload (PDF/JPEG/PNG, ≤10MB)
  → MIME + size validation                    (UploadService.ingest)
  → vector-PDF text extraction (pdfminer.six)  (app/nlp/ocr.py)
  → OCR fallback if <50 tokens extracted       (Tesseract, lang=deu, PSM 6)
  → text normalisation                         (soft-hyphen/line-break cleanup)
  → sentence splitting                         (spaCy de_core_news_lg, regex fallback)
  → numeric extraction                         (premium/deductible/limit regex, German amount format)
  → clause classification                      (gBERT zero-shot, keyword fallback)
  → coverage/exclusion concept mapping         (German→English controlled vocabulary)
  → persisted as Upload.extracted (JSON) + canonical Clause rows (upload_id FK)
```

Every stage degrades gracefully rather than failing hard: if spaCy or the
gBERT model aren't available in the runtime (e.g. a slim container build),
the pipeline falls back to a deterministic regex sentence splitter and a
keyword-based classifier — the same public `ClauseExtractor.extract()`
surface is used either way, so the rest of the application doesn't care
which mode ran. This is why the pipeline is testable and tested
end-to-end without needing the ML models installed
(`backend/tests/test_nlp.py` forces the fallback path deliberately).

## Clause taxonomy

`app.db.enums.ClauseType`:

`COVERAGE` · `EXCLUSION` · `LIMIT` · `DEDUCTIBLE` · `OBLIGATION` ·
`DEFINITION` · `TERRITORIAL_SCOPE` · `DURATION` · `OPTIONAL_BENEFIT` ·
`OTHER`

The keyword-fallback classifier (`app/nlp/extractor.py::_keyword_classify`)
has an explicit German keyword list per type (e.g. `selbstbehalt` /
`selbstbeteiligung` → `DEDUCTIBLE`; `geltungsbereich` / `weltweit` →
`TERRITORIAL_SCOPE`), checked in a fixed priority order so overlapping
keywords resolve predictably.

## Confidence and honesty

- OCR confidence is Tesseract's real mean character-confidence
  (`pytesseract.image_to_data`), not a fabricated number. Below
  `OCR_CONFIDENCE_THRESHOLD` (70, configurable), a warning is attached to
  the upload and surfaced in the UI.
- The keyword-fallback classifier reports a fixed confidence of 0.6–0.7
  (lower than the ML path's real softmax score) precisely so the UI can
  distinguish "the model was actually confident" from "this is the
  deterministic fallback's best guess" — it is not tuned to look more
  certain than it is.
- Low-confidence extractions are shown with an explicit warning
  ("Low extraction confidence — please review the source clause" /
  German equivalent), never silently hidden.

## Provenance

Every `Clause` row derived from a user upload carries:
`upload_id` (which document), `document_language` (`"de"`),
`extraction_method` (`ocr_nlp`), `page_number`, `confidence`, and the
verbatim `text`. Catalogue clauses (if an admin adds real sourced ones,
see `docs/DATA_SOURCES.md`) instead carry `policy_id` and
`extraction_method="seed"` or `"manual"`. A clause is never linked to both.

## Scope

- Language: German only (Austrian insurance documents). No multi-language
  document support — this matches the frozen project scope, not an
  oversight (the *UI* is bilingual EN/DE; the *documents processed* are
  always German).
- Product lines: car/household/travel/legal, matching the catalogue scope
  (`docs/DATA_SOURCES.md`).
