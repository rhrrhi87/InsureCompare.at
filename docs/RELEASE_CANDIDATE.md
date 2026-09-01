# Release Candidate

File: `docs/RELEASE_CANDIDATE.md`
Status date: 2026-08-28 (repository freeze), updated 2026-08-29 (AI Policy Advisor)
Prepared by: Claude (this session), acting as lead engineer on this codebase

## Version / status

**Academic prototype release candidate**, prepared for the SWE6010 BEng
Software Engineering dissertation submission at the University of Greater
Manchester. Not committed to git as of this document's writing. The
2026-08-28 pass was a consistency/cleanup/documentation freeze with no new
product features. The 2026-08-29 pass added one new, scoped feature — the
AI Policy Advisor — on top of that frozen state, per explicit instruction;
it does not reopen or modify anything the freeze had already settled
(recommendation engine, OCR/NLP pipeline, provider catalogue, real-document
evidence).

## Implemented scope

- Full-stack app: FastAPI + SQLAlchemy 2.0 (async) + Alembic backend,
  React 18 + TypeScript + Vite + Tailwind frontend, PostgreSQL 16 database.
- Authentication (JWT access/refresh with rotation), role-based access
  (user/admin), session management.
- Insurance policy catalogue with filtering, 2–3-way comparison, and a
  weighted-additive, fully explainable recommendation engine (per-factor
  score breakdown, methodology card, narrative explanation).
- Document upload → OCR (Tesseract, with vector-PDF text extraction tried
  first) → NLP clause extraction (zero-shot classification + a
  keyword/regex fallback) → structured, evidence-linked clauses with
  page number and confidence, traceable back to the source upload.
- Admin console: provider/policy CRUD, document review, audit log.
- Full EN/DE bilingual UI (react-i18next), including dynamic `<html lang>`
  and a language switcher that never alters domain data or scores.
- Playwright E2E suite (8 user journeys + 2 Advisor journeys) and an
  automated axe-core accessibility scan (10 page states).
- **AI Policy Advisor** (KI-Versicherungsberater): an evidence-grounded
  RAG explanation layer over a single uploaded document, added after the
  existing OCR/NLP pipeline (not replacing it). Google Gemini
  (`gemini-3.6-flash`) is the reasoning provider server-side only; a
  deterministic mock provider is used for all automated tests. See
  `docs/AI_ADVISOR_ARCHITECTURE.md`.

## Real-data scope

Real, official Austrian insurer documents were used to **validate the
document-understanding pipeline**, end to end:

| What | Result |
|---|---|
| Documents ingested | 3 real IPIDs — UNIQA (Kfz-Haftpflicht), Generali (Haushalt), Wiener Städtische (Rechtsschutz) |
| Source verification | Downloaded directly from each insurer's own domain/CDN; sha256-checked; full metadata in `backend/data/source_documents/MANIFEST.json` |
| Ingestion | Via the real `POST /api/documents` endpoint (not a DB insert) |
| Extraction | 148 real clauses, genuine pipeline output, page-numbered and confidence-scored |
| Real hand-labelled evaluation set | 59 examples, ground truth from manual reading of the real documents |
| Provenance classification | `VERIFIED_SOURCE` (documents) + `DOCUMENT_EXTRACTED` (clauses) — see `docs/DATA_PROVENANCE_AUDIT.md` §4a |

**This validates document understanding, not the pricing catalogue** — see
Academic Claim Boundaries below.

## Synthetic/demo-data scope

- The comparison/recommendation catalogue: **12 `Policy` rows, all
  `is_demo_data=true`**, across 6 of the 15 providers. Premiums, coverage
  items, exclusions, and deductibles are illustrative, hand-authored
  examples — never transcribed from a real document.
- All 15 `Provider.rating_score` values are a uniform placeholder (8.0) —
  no real, sourced insurer rating feed exists.
- The NLP evaluation's "controlled" fixture set (60 clause-classification
  examples, 24 extraction examples, 8 vocabulary examples) is
  hand-authored, used because the project originally had no real documents
  to evaluate against; kept for continuity alongside the real-document
  results.
- The frontend now visibly labels demo/synthetic pricing wherever it is
  most likely to be mistaken for a live quotation: the Compare page
  (when any listed policy is demo data), the Recommendations page's "Best
  Match" hero card and "All Policies Ranked" section, and the Policy
  Detail page — all using the existing "Demonstration data" /
  "Demonstrationsdaten" badge.

## Real source documents used

| Insurer | Product | Document type | Official source URL |
|---|---|---|---|
| UNIQA Österreich Versicherungen AG | Auto & Frei (Kfz-Haftpflicht) | IPID | uniqa.at/versicherung/f/172351/x/297ae8c004/uat_ipid_kfz-haftpflicht.pdf |
| Generali Versicherung AG | Haushaltversicherung | IPID | eu-assets.contentstack.com/.../IPID_SachHaushalt_244001.pdf (linked from generali.at) |
| WIENER STÄDTISCHE Versicherung AG – VIG | Rechtsschutzversicherung | IPID | wienerstaedtische.at/fileadmin/user_upload/Dokumente/IPID/IPID_NKS_Rechtsschutzversicherung.pdf |

Full metadata (title, version date, retrieval date/method, sha256,
language): `backend/data/source_documents/MANIFEST.json` (tracked in git).
**The PDFs themselves are not committed** — redistribution permission for
third-party insurer PDFs is unclear even though they are freely publicly
accessible; see `docs/DATA_PROVENANCE_AUDIT.md` §8. Reproduce with:

```bash
cd backend
python -m scripts.download_source_documents
python -m scripts.ingest_real_documents   # requires the dev server running
python -m scripts.evaluate_nlp
```

## NLP results (measured, not estimated — preserved exactly)

| | Synthetic (60 examples) | **Real documents (59 examples)** |
|---|---|---|
| Keyword fallback — accuracy / macro-F1 | 0.700 / 0.715 | **0.559 / 0.490** |
| Zero-shot gBERT — accuracy / macro-F1 | 0.400 / 0.361 | **0.322 / 0.226** |

Both classifiers are weaker on real documents than on synthetic data — an
experimental finding about the pipeline's real-world generalisation, not a
software failure, and not hidden. Full per-class breakdown, confusion
matrices, and the specific real failure modes (e.g. the zero-shot model
misclassifying all 10 real `coverage` examples as `obligation`) are in
`docs/NLP_EVALUATION.md`. Numeric extraction and vocabulary matching were
evaluated only on synthetic data (real IPIDs don't disclose the
premium/deductible/limit figures those extractors look for).

## OCR results (measured, not estimated — preserved exactly)

| | Synthetic (clean/small-font) | **Real document (genuine test)** |
|---|---|---|
| Tesseract mean confidence | 94.1% / 85.1% | **92.6%** |
| CER / WER | 0.000–0.008 / 0.000–0.077 | **0.562 / 0.690** |
| Order-independent word-overlap F1 | — | **0.982** |

The real-document CER/WER looks alarming in isolation but is explained,
not hidden: 98.2% of individual words were recognised correctly
(consistent with the 92.6% confidence); the high CER/WER comes from the
real document's two-column "Was ist versichert? / Was ist nicht
versichert?" layout defeating single-block OCR's (`--psm 6`) reading
order — a document-layout-analysis limitation, not a character-recognition
failure. Full explanation in `docs/NLP_EVALUATION.md` and
`docs/DATA_PROVENANCE_AUDIT.md` §6.

## AI Policy Advisor

Public name: **AI Policy Advisor** / **KI-Versicherungsberater** — Gemini
is an implementation detail, never surfaced in the product name.

| Aspect | Design |
|---|---|
| Reasoning provider | Google Gemini, `gemini-3.6-flash`, via the official `google-genai` SDK — server-side only, never exposed to the frontend |
| Retrieval | Lexical term-overlap ranking over the *current document's own* clauses only (no pgvector — disclosed as a deliberate scope decision, see `docs/AI_ADVISOR_ARCHITECTURE.md` §3) |
| Grounding | If no clause is lexically relevant, the LLM is never called — a fixed "cannot be confirmed" response is returned directly |
| Evidence validation | Every `evidence_id` the LLM returns is checked against the exact set of clause IDs actually offered to it in that call; anything else is discarded before it reaches the client |
| Structured output | Two Pydantic schemas (`AdvisorResponse`, `AdvisorSummary`) requested via Gemini's JSON-schema response mode; malformed output is treated as a provider failure, not a crash |
| PII minimisation | Regex redaction (email/IBAN/phone/reference numbers) applied to every clause and question before it leaves the process |
| Prompt-injection framing | Evidence is always wrapped in an explicit "this is DATA, not instructions" block, in both languages |
| Testing | 25 backend tests + 2 Playwright E2E tests, all against `LLM_PROVIDER=mock` (deterministic, offline) |
| Cost control | Per-document summary cached (`Upload.advisor_summary`); fetched only when the user expands the panel; capped context (≤8–16 clauses, 400 chars each) and output tokens |

Full architecture, anti-hallucination design, and disclosed known
limitations (lexical-only retrieval, regex-only PII redaction, no
Comparison Advisor UI): `docs/AI_ADVISOR_ARCHITECTURE.md`.

### Live Gemini API test

**LIVE GEMINI TEST: PASSED on 2026-08-29.** The first real call established
that `gemini-2.5-flash` is unavailable to new users (404); the configured
model was therefore updated to Google's stated replacement,
`gemini-3.6-flash`. A controlled request then authenticated, completed, and
parsed as the project's `AdvisorResponse` schema.

The real Advisor was subsequently executed against upload 16,
`generali_haushalt_ipid.pdf` (47 extracted PostgreSQL clauses). German and
English supported questions about intentional damage returned clause 101;
the backend confirmed the ID belonged to upload 16 and the returned source
text was byte-for-byte the PostgreSQL clause text. Deliberately unsupported
Mars-coverage questions returned `supported=false`, no evidence, and no
invented policy facts. Automated suites remain pinned to
`LLM_PROVIDER=mock` and never make network calls.

```bash
# backend/.env: LLM_PROVIDER=gemini, GEMINI_API_KEY=<your real key>
cd backend
python -m scripts.download_source_documents   # if not already present
python -m scripts.ingest_real_documents        # requires the dev server running
# then, with the dev server running and a browser session logged in:
#   POST /api/uploads/<id>/advisor/ask
#   {"question": "Welche wichtigen Ausschlüsse enthält dieses Dokument?", "language": "de"}
```

## Backend test results

```
58 passed, 28 warnings — pytest -q   (33 pre-existing + 25 in test_advisor.py)
```

Alembic migrations apply cleanly to a real PostgreSQL 16 instance
(`alembic upgrade head`, idempotent, no pending revisions) — including the
new `0003_advisor_summary` migration (adds a nullable `advisor_summary`
JSON column to `uploads`, no data migration required).

## Frontend test results

```
npm run typecheck   → clean, 0 errors
npm run lint        → clean, 0 errors/warnings
npm test            → 3 files, 13 tests passed (vitest)
npm run build       → succeeds, ~630 kB JS (188 kB gzip)
```

## E2E / accessibility results

```
npx playwright test   → 19/19 passed
  - 8 named user journeys (landing, language switch, login, browse,
    compare, recommend, upload+OCR/NLP, admin providers/policies)
  - 2 AI Policy Advisor journeys (supported answer with real DB evidence;
    refuses to confirm coverage the document does not mention)
  - 10 axe-core accessibility scans (landing, login, register, dashboard,
    compare, recommendations, upload — collapsed and Advisor-expanded,
    admin providers, admin policies)
    → 0 violations on all 10, after fixing 7 real, disclosed defects total
      (6 from the original audit; 1 new contrast regression in the
      Advisor's note text, fixed the same session it was introduced)
```

Full detail: `docs/TESTING.md`, `docs/ACCESSIBILITY.md`,
`docs/AI_ADVISOR_ARCHITECTURE.md`.

## Known limitations

- The comparison/recommendation catalogue is entirely `DEMO_SYNTHETIC` —
  no real, priced insurer product exists in the catalogue.
- Only 3 real source documents exist, across 3 of 15 providers and 3 of 4
  product lines (no real travel-insurance IPID). The real-document
  NLP/OCR results are an initial genuine sample, not an exhaustive
  benchmark.
- Neither clause classifier is production-ready; the keyword fallback
  measurably and consistently outperforms the zero-shot model on both
  synthetic and real data.
- OCR reading order breaks down on real multi-column layouts (character
  recognition itself is strong).
- No screen-reader (JAWS/NVDA/VoiceOver) pass has been performed; the
  accessibility review is automated (axe-core) plus manual code-level
  checks only.
- Form validation errors are not wired to `aria-describedby`.
- Docker Compose path is provided as-is and has not been run end-to-end in
  this project's own sessions (native setup is the fully-verified path).
- The AI Policy Advisor's retrieval is lexical keyword overlap, not
  semantic search — a question in a different language than the
  document's own text will not match. PII redaction is regex-based only
  (no NER). No Comparison Advisor UI was built. The live Gemini API path
  has not been exercised in this environment (no API key configured) —
  see `docs/AI_ADVISOR_ARCHITECTURE.md` "Known limitations" for the full
  list.

## Reproduction instructions

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download de_core_news_lg
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev

# Optional — reproduce the real-document evaluation
cd backend
python -m scripts.download_source_documents
python -m scripts.ingest_real_documents
python -m scripts.evaluate_nlp

# Optional — full test suite
cd backend && pytest -q
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
cd frontend && npm run e2e   # requires both dev servers running

# Optional — enable the real Gemini API (leave LLM_PROVIDER=mock to skip)
# Edit backend/.env: LLM_PROVIDER=gemini, GEMINI_API_KEY=<your key>
```

Demo accounts: `user@test.at` / `user123` (user), `admin@insurance.at` /
`admin123` (admin).

## Academic claim boundaries

State this project's scope accurately:

- ✅ "The prototype evaluates document understanding — ingestion, OCR,
  clause extraction, and clause classification — on real official
  Austrian insurance documents."
- ✅ "Controlled synthetic policy and pricing data is used for parts of
  the comparison and recommendation demonstration where authoritative
  comparable pricing is unavailable."
- ✅ "Zero-shot clause classification is weak (32–40% accuracy) and the
  keyword fallback classifier measurably outperforms it; neither is
  production-ready."
- ✅ "OCR character recognition is strong on real content, but reading
  order fails on multi-column layouts."
- ❌ Do not say "recommendations are based entirely on live/real insurer
  quotations."
- ❌ Do not say "InsureCompare currently compares live Austrian insurance
  prices."
- ❌ Do not say or imply that any of the 15 providers endorse, partner
  with, or are affiliated with InsureCompare.at — their names and logos
  are used only to identify real, well-known companies as catalogue
  labels and evaluation subjects.
- ✅ "The AI Policy Advisor explains an uploaded document using only that
  document's own extracted clauses; it does not answer from generic
  insurance knowledge, and says so explicitly when the evidence doesn't
  support an answer."
- ❌ Do not say the Advisor has been validated against a live Gemini API
  call in this environment — it has not (no key configured); it has been
  validated end-to-end against the deterministic mock provider only.
- ❌ Do not describe InsureCompare.at as a licensed insurance broker or a
  provider of regulated financial advice — see `/legal` (Rechtliche
  Hinweise / Legal Information) for the accurate, non-academic-framed
  public disclosure, and the "academic research prototype" framing itself
  belongs only in academic documentation (this file, README.md, and the
  other `docs/` files), never in normal product-facing UI.
