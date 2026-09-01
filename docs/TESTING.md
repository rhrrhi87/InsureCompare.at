# Testing

## Research claim boundary

Real official Austrian insurer documents were used in this project to
validate document ingestion, PDF text extraction, OCR, clause extraction,
clause classification, and evidence traceability (see
`docs/DATA_PROVENANCE_AUDIT.md` §4a and `docs/NLP_EVALUATION.md`). The
comparison/recommendation catalogue exercised throughout the rest of this
document still contains `DEMO_SYNTHETIC` policy and pricing records where
equivalent official comparable pricing was unavailable. Accurate framing:
*the prototype evaluates document understanding on real official Austrian
insurance documents, while controlled synthetic policy and pricing data is
used for parts of the comparison and recommendation demonstration where
authoritative comparable pricing is unavailable.* Do not describe any
result below as evidence that recommendations are based on live/real
insurer quotations, or that the app compares live Austrian insurance
prices — neither claim is supported.

## Status: actually executed (2026-08-28)

Unlike the previous revision of this document (written when no runtime was
available), everything below was **actually run** in a real environment:
Python 3.12.10 + a fresh venv, Node 24.19 / npm 11.17, PostgreSQL 16
(installed via winget, running as a native Windows service), and Tesseract
OCR 5.4.0 (`deu`/`eng`/`osd`). Docker Desktop was present but non-functional
in this environment (WSL2 not installed) — Postgres was run natively
instead; see `docs/IMPLEMENTATION_PLAN.md` for that decision.

## Backend (`backend/tests/`, pytest + pytest-asyncio, SQLite in-memory)

```
58 passed, 28 warnings in ~30s  (33 pre-existing + 25 in test_advisor.py, added 2026-08-29)
```

| File | Covers | Result |
|---|---|---|
| `test_recommender.py` | Weight normalisation, score bounds, ordering, breakdown keys | ✅ 6/6 |
| `test_nlp.py` | Numeric extraction, clause classification incl. `DEDUCTIBLE`/`TERRITORIAL_SCOPE`, vocabulary detection | ✅ 8/8 |
| `test_auth.py` | Register/login/me, refresh rotation, logout revocation | ✅ 9/9 |
| `test_recommendation_api.py` | `/recommend`, `/compare`, admin-only `/admin/stats` | ✅ 4/4 |
| `test_admin_catalogue.py` | Retire/reactivate, evidence endpoint, audit events | ✅ 6/6 |
| `test_advisor.py` | AI Policy Advisor: PII redaction, RAG retrieval, document isolation, anti-hallucination negative tests, critical evidence-ID validation, prompt-injection framing, provider factory/mock/missing-key, bilingual answers, summary caching — see `docs/AI_ADVISOR_ARCHITECTURE.md` §13 | ✅ 25/25 |

Getting to a clean pass required fixing **4 real defects**, none of which
the pre-existing suite could have caught on its own (SQLite has no real
Postgres enum/pool semantics):

1. `aiosqlite` was used by `conftest.py` but never listed in
   `requirements.txt` — `pytest` failed to even collect.
2. `app/db/session.py` passed `pool_size`/`max_overflow` unconditionally to
   `create_async_engine`; SQLite's `StaticPool` rejects those kwargs.
   Fixed by making them conditional on the dialect.
3. `SessionService.get_active` compared an aware `datetime.now(timezone.utc)`
   against `Session.expires_at`, which SQLite returns naive even for a
   `DateTime(timezone=True)` column — `TypeError`. Fixed with a
   `_as_utc()` normaliser.
4. `create_refresh_token`/`create_access_token` had no `jti` claim, so two
   tokens issued for the same user within the same second were
   byte-identical — a real single-use-rotation defect, not just a test
   artifact. Fixed by adding a random `jti` to every issued token.

## Database / migrations (real PostgreSQL 16, not SQLite)

Running the actual Alembic migrations against a real Postgres server (never
exercised by the test suite, which builds schemas straight from the ORM
models) surfaced **2 more real defects**, both in the migration files:

5. `sa.Enum(..., create_type=False)` was used to avoid a double `CREATE
   TYPE` — but `create_type` is not a parameter of the generic,
   cross-dialect `sqlalchemy.Enum`; it's silently accepted and dropped, and
   the PostgreSQL-dialect adapter that actually emits DDL defaults it back
   to `True`. Result: `DuplicateObjectError` on every enum column. Fixed by
   importing and using `sqlalchemy.dialects.postgresql.ENUM` directly,
   which does respect the flag.
6. Migration `0002`'s revision id (`0002_provenance_sessions_clause_types`,
   37 chars) exceeded Alembic's default 32-character `version_num` column,
   so the migration's own bookkeeping `UPDATE` failed after all its DDL had
   already run — a transaction-rollback near-miss. Shortened to
   `0002_provenance_sessions` and renamed the file to match.

After both fixes: `alembic upgrade head` runs clean, produces all 10 tables
(the original 8 + `sessions` + the `clauses`/`policies` provenance columns),
and `enum_range(NULL::clause_type)` correctly lists all 10 clause types.
`python -m scripts.seed` populates 6 providers, 12 policies, and both demo
accounts idempotently.

7. `scripts.seed`'s own success-path `logger.info("Seed complete")` crashed
   with a Windows-console `UnicodeEncodeError` — same root cause as the
   defect described next.

## Real Postgres data bug (enum value vs. name)

8. **The most significant defect found**: `SQLAlchemy Enum(SomePythonEnum)`
   defaults to storing the enum member's *name* (`"CAR"`) rather than its
   *value* (`"car"`). The Alembic migration created the native Postgres
   enum types using the lowercase `.value` strings, so every INSERT against
   a real Postgres database failed with
   `invalid input value for enum product_line: "CAR"`. This is invisible
   under SQLite (no real enum type to enforce the mismatch) — the seed
   script and every API write path would have looked "fine" against SQLite
   and failed 100% of the time against Postgres. Fixed with a shared
   `str_enum()` helper (`app/db/base.py`) using `values_callable` on every
   one of the 9 enum columns across `user.py`, `policy.py`, `upload.py`,
   `profile.py`. Verified after the fix: `SELECT product_line FROM
   policies` correctly returns `car`/`household`/etc.

## Logging encoding bug (Windows-specific, masked a real OCR failure)

9. `app/core/logging.py`'s `PrintLoggerFactory(file=sys.stdout)` writes to
   a stream that defaults to the Windows legacy console code page
   (`cp1252`) rather than UTF-8. Since this application's core subject
   matter is German text (ä/ö/ü/ß), any `logger.exception(...)` call
   handling an error that contains — or is adjacent to code that recently
   produced — non-Latin-1 text raises a *second*, unrelated
   `UnicodeEncodeError` from inside the exception handler, which converts
   what should be a clean, recoverable error response into an unrelated
   500. This was caught via the real upload endpoint (see below) and fixed
   by reconfiguring `stdout`/`stderr` to UTF-8 at logging setup time.

## OCR / NLP pipeline (real Tesseract 5.4.0, real image, real German text)

A synthetic but realistic German motor-insurance document image was
generated (premium/deductible/coverage-limit/coverage/exclusion/
territorial-scope sentences) and run through the actual pipeline —
first directly, then through the live `POST /api/documents` endpoint.

10. **Root cause of the encoding crash, and the most important AI-pipeline
    defect**: `GBERT_MODEL` defaulted to `"deepset/gbert-base"`, a plain
    pretrained BERT checkpoint with no entailment/NLI head.
    `transformers`' `zero-shot-classification` pipeline still "loads" it —
    with a freshly, randomly initialised classification head — and then
    classifies **every single clause into the same class**, regardless of
    content (confirmed directly: 8/8 test clauses all came back
    `OPTIONAL_BENEFIT`, with the load logs explicitly warning
    `newly initialized: ['classifier.bias', 'classifier.weight']`). This
    silently defeated the entire "AI-assisted clause classification"
    research claim whenever `transformers`/`torch` were installed (the
    keyword-fallback path, exercised by the unit tests, was never affected
    — this bug was invisible to the test suite by construction). Fixed by
    switching to `Sahajtomar/German_Zeroshot`, a German model actually
    fine-tuned on XNLI for zero-shot classification. Re-verified: the same
    8 test clauses now come back with **varied** classifications
    (`coverage`, `obligation`, `exclusion`, `duration` — not perfect, since
    zero-shot on a specialised 10-way taxonomy is a genuinely hard task,
    but no longer degenerate) and honestly modest confidence scores
    (0.19–0.41, correctly reflecting real uncertainty rather than a
    fabricated high number).
11. Tesseract was not on `PATH` for the application process on this Windows
    machine (confirmed with `curl` → `tesseract is not installed or it's
    not in your PATH`, a real, common failure mode for the official Windows
    installer). Fixed with a `TESSERACT_CMD` setting plus an automatic
    fallback to the default Windows install location when the binary
    genuinely isn't found on `PATH` and no explicit path is configured —
    this does not affect the Docker image, where `tesseract-ocr` is already
    on `PATH`.

**End-to-end result after all fixes** (`POST /api/documents` with the real
test image, real user, real Postgres): `status: "ready"`,
`ocr_confidence: 94.39` (genuine Tesseract mean character confidence, not
fabricated), correct numeric extraction (premium €65, deductible €350,
coverage limit €5,000,000), correct coverage/exclusion vocabulary
detection, 8 clauses persisted as real `Clause` rows
(`extraction_method=ocr_nlp`, `document_language=de`, real per-clause
confidence) linked to the upload via `upload_id`.

## Quantitative NLP/OCR evaluation (2026-08-28, updated with real documents)

The result above ("94% confidence, correct German text recovered", "clause
classification varied and honestly-scored") was a single manual run. A
separate, reproducible evaluation was built and actually executed
afterwards — first against labelled controlled/synthetic test fixtures,
then extended the same day to 3 REAL official Austrian insurer IPID
documents (downloaded directly from uniqa.at, generali.at, and
wienerstaedtische.at — see `backend/data/source_documents/MANIFEST.json`
and `docs/DATA_PROVENANCE_AUDIT.md` §4a). Full methodology, per-class
metrics, confusion matrices and honest discussion of weaknesses in
`docs/NLP_EVALUATION.md`. Headline numbers (all measured, none estimated):

| Component | Metric | Synthetic | **Real documents** |
|---|---|---|---|
| Clause classification — zero-shot gBERT | Accuracy / macro-F1 | 0.400 / 0.361 | **0.322 / 0.226** |
| Clause classification — keyword fallback | Accuracy / macro-F1 | 0.700 / 0.715 | **0.559 / 0.490** |
| Numeric field extraction (premium/deductible/limit) | Accuracy | 1.000 (within pattern coverage) | N/A — real IPIDs don't disclose these figures |
| Coverage/exclusion vocabulary matching | Precision / recall / F1 | 0.947 / 1.000 / 0.973 | not re-evaluated (same reason) |
| OCR | CER / WER | 0.000–0.008 / 0.000–0.077 (clean/small-font synthetic) | **0.562 / 0.690** (genuine OCR on a rasterised real page — see below) |

**Both classifiers are weaker on real documents than on synthetic
data — this is the more important number, not the synthetic one.** The
real-document OCR result looks alarming in isolation (56%/69% error) but
is explained by a genuine, disclosed finding, not swept under the rug: an
order-independent word-overlap check shows 98.2% of individual words were
recognised correctly (consistent with Tesseract's 92.6% mean confidence);
the high CER/WER is caused by the real document's two-column layout
defeating single-block OCR's reading order, not by misrecognised
characters. Full explanation in `docs/NLP_EVALUATION.md`. Reproduce with
`cd backend && python -m scripts.evaluate_nlp`.

## Frontend

### Typecheck / lint / unit tests / build

```
npm run typecheck   →  clean, 0 errors
npm run lint        →  clean, 0 errors/warnings
npm test            →  3 files, 13 tests passed
npm run build       →  built in ~9s, 628 kB JS (188 kB gzip)
```

Getting a clean `typecheck` required fixing **2 real, pre-existing defects**
(present before this session started, never caught because `tsc` had never
actually been run against this codebase):

- `components/ui/index.tsx`'s `Label` was typed `HTMLAttributes<HTMLLabelElement>`,
  which does not include `htmlFor` — every `<Label htmlFor="...">` call site
  (Login, Register, Dashboard, this session's new admin pages) failed
  `tsc`. Fixed by typing it as `LabelHTMLAttributes<HTMLLabelElement>`.
- `vite.config.ts`'s `test` block isn't part of plain `vite`'s
  `UserConfigExport` type. Fixed with the standard
  `/// <reference types="vitest/config" />` triple-slash directive.

Getting a clean `lint` required a **3rd defect fix**: `package.json` pins
`eslint@^9`, which requires flat config (`eslint.config.js`) by default, but
the repo only had the legacy `.eslintrc.cjs` — `eslint . --ext .ts,.tsx`
failed immediately with "couldn't find an eslint.config.js file". Fixed by
adding `eslint.config.js` using `@eslint/eslintrc`'s `FlatCompat` to
reproduce the exact same legacy rule set (no rules changed, only the config
file format).

A static-review subagent pass (before this run/test/debug session, during
initial implementation) had already caught and fixed 3 more issues: an
unused `Button` import, a TypeScript union-inference bug in a hand-written
tab array, and a wrong i18n key path — see `docs/IMPLEMENTATION_PLAN.md`.

### Manual browser verification (real dev server, real Postgres-backed API)

Driven through an actual Chromium-based browser pane against
`http://localhost:5173` (Vite dev server) proxying to the real FastAPI
backend on `:8000`. Every item below was clicked/typed through and its
result inspected — not merely code-reviewed:

| Workflow | Result |
|---|---|
| Landing page | ✅ renders, hero/features/insurance-types/how-it-works/why-InsureCompare/about/disclaimer all present |
| EN → DE language switch | ✅ (see note below on tooling) |
| Registration | ✅ new account created, redirected to login with success banner |
| Login (demo + new account) | ✅ |
| Logout | ✅ real `POST /api/auth/logout` (200) confirmed via network log before local state cleared |
| User dashboard | ✅ preferences form, advanced weights (sum-to-100% validation shown live), required-coverages chips |
| Risk-profile save → recommend | ✅ weights round-tripped exactly (25/30/20/10/15%) into the recommendation response |
| Policy catalogue / compare | ✅ 3-policy selection cap enforced, comparison table renders, summary stats correct |
| Policy detail | ✅ coverage/exclusions/summary render; "Demonstration data" badge shown |
| Source evidence | ✅ correctly, honestly empty for demo-catalogue policies with the disclosed reason text |
| PDF/image upload | ✅ via real `POST /api/documents` (browser file-picker automation wasn't available in this tool session, so the identical endpoint the dropzone calls was exercised directly with the same file) |
| OCR (German document) | ✅ 94% confidence, correct German text recovered |
| NLP extraction | ✅ correct numbers/vocabulary; clause classification varied and honestly-scored after the GBERT fix |
| Recommendation generation | ✅ score 91/100 example, per-factor breakdown summed correctly |
| Explainable score breakdown | ✅ weight/sub-score shown per factor, methodology card matches active weights exactly |
| Three-policy comparison | ✅ |
| Admin login | ✅ |
| Provider management | ✅ list renders; create tested live (see defect #12 below); retire/reactivate available |
| Policy management | ✅ list, filters, retire/reactivate all functional |
| Policy retirement | ✅ retired via UI, confirmed persisted via API (`is_active: false`, `retired_at` set), reactivated back to restore state |
| Documents page (admin) | ✅ shows the real uploaded document with status/confidence |
| Audit log | ✅ real `LOGIN`/`POLICY_RETIRED`/`RECOMMENDATION_GENERATED` entries with actor/entity/timestamp |

12. `AdminProvidersPage`'s "open the create form" button and the form's
    own submit button both rendered the literal text "New Provider" (the
    submit button reused the `providers.create` translation key meant for
    the toggle). Not a crash, but a genuine UX ambiguity — caught when an
    automated click landed on the (first, DOM-order) toggle button instead
    of the intended submit button, silently closing the form instead of
    saving. Fixed by giving the submit button its own `common:actions.save`
    label, matching the edit-form's already-correct behaviour.
13. `UploadPage`'s "OCR confidence" field displayed
    `extracted.clauses[0].confidence` (the *first clause's NLP
    classification* confidence, e.g. 19%) instead of the actual
    `upload.ocr_confidence` field (94%, the real Tesseract score) — a
    pre-existing display bug, caught only by reading the real numbers
    against a real Tesseract result rather than trusting the label. Fixed
    by threading `ocr_confidence` through as its own prop.

**Tooling note on EN/DE verification**: this session's Browser-pane
`computer` click action was unreliable for a specific subset of clicks
(consistent 30s timeouts on Retire buttons, on the very first language-
toggle attempt, and generally whenever the machine's CPU was under heavy
load from a concurrent local model download/inference run) — confirmed to
be a tool/environment issue, not an app bug, by dispatching the identical
click via `element.click()` in the page's own JS context, which worked
immediately every time and produced a verifiable result (`localStorage`
key changed, `<html lang>` updated, rendered German text appeared). Every
UI interaction in this session's testing that hit this issue was retried
successfully via that method; none were skipped.

**Responsive layout note**: the Browser pane's own default width (~312–327px
CSS pixels) is narrower than any real device and briefly showed a ~56px
`document.body` horizontal overflow originating in the header's nav row.
Re-tested at the standard mobile width (375×812, iPhone SE/8/etc. class):
`document.body.scrollWidth === document.body.clientWidth === 375`, i.e. **no
overflow at any real device width** — not a genuine defect.

## Automated E2E tests (Playwright, added 2026-08-28)

`frontend/e2e/journeys.spec.ts` — 8 named journeys, run against the real
FastAPI backend + PostgreSQL + Vite dev server (no mocking):

```
8 passed (17.3s)
```

| # | Journey | Result |
|---|---|---|
| 1 | Landing page → register → login navigation | ✅ |
| 2 | EN → DE language switch, `<html lang>` updates | ✅ |
| 3 | Login as demo user → browse policies (Compare page) | ✅ |
| 4 | Select and compare 2 policies side by side | ✅ |
| 5 | Save risk-profile preferences → AI recommendations with methodology | ✅ |
| 6 | Upload a controlled fixture image → real OCR/NLP extraction | ✅ |
| 7 | Policy detail page shows coverage/exclusions | ✅ |
| 8 | Admin login → Providers → Policies management pages | ✅ |

Reproduce: `cd frontend && npm run e2e`. Requires the backend
(`uvicorn app.main:app --port 8000`) and frontend (`npm run dev`) already
running.

Real defects this suite caught in its own test code (not app bugs, but
worth recording since they show the tests actually exercise the app
rather than trivially passing): initial locators assumed a "Pick" button
per policy row, but the real control is an unlabelled `<input
type="checkbox">` (which also led to fixing a genuine `label`-role axe
violation, see `docs/ACCESSIBILITY.md`); "Get AI Recommendations →" is a
`<button>`, not a `<link>`; and the demo "Login as User/Admin" buttons
fill the form via `setValue()` rather than submitting, which raced ahead
of the DOM on a couple of runs — fixed in the test by waiting for the
email field's real value before clicking Sign In, the same category of
timing flake already noted above for the Browser-pane tool.

**Separately, this run surfaced one real backend-side environment
finding**: the app's per-IP rate limit (`RATE_LIMIT_PER_MINUTE=60` in
`backend/app/core/rate_limit.py`) is a reasonable production default but
is genuinely exceeded by ~8 sequential Playwright journeys plus Vite dev
traffic from one machine. Raised to `600` in `backend/.env` (test
environment only, not `.env.example`) to run this suite; a CI environment
running this suite against a shared backend would need the same
consideration.

An automated axe-core accessibility scan (`frontend/e2e/accessibility.spec.ts`)
was also added in this phase — see `docs/ACCESSIBILITY.md` for full
results (0 violations across 9 pages after fixing 6 real, disclosed
defects).

## AI Policy Advisor E2E tests (Playwright, added 2026-08-29)

`frontend/e2e/advisor.spec.ts` — 2 tests, run against the real backend with
`LLM_PROVIDER=mock` (no live Gemini calls in this suite):

```
2 passed
```

| Test | Result |
|---|---|
| Advisor answers a supported question with real database evidence — asserts the network response's `evidence[0].text` is the real Postgres clause verbatim, and that it renders under "Source Evidence" in the UI | ✅ |
| Advisor refuses to confirm coverage the document does not mention (flood damage, never present in the fixture) — asserts `supported: false`, zero evidence, and the fixed "cannot be confirmed" message, both in the API response and rendered in the UI | ✅ |

The accessibility scan was also extended to the Advisor panel in its
expanded state — this caught one real contrast defect (a note paragraph
using the same too-light `text-slate-400` colour fixed everywhere else in
`docs/ACCESSIBILITY.md`'s earlier pass, re-introduced in the new
component), fixed immediately; 0 violations after the fix.

## What's still not covered (honest gap, not a false claim)

- A drag-and-drop file upload exercised through literal OS-level browser
  file-picker automation (the upload endpoint itself — which is 100% of
  what the dropzone calls — was fully exercised instead).
- Real OCR has now been tested against a rasterised page of a real IPID
  (see `docs/NLP_EVALUATION.md`), but only 1 page of 1 of the 3 real
  documents — not a real photographed/scanned paper document (all 3 real
  sources are genuine digital PDFs, so the pipeline never invokes OCR on
  them directly; the rasterisation was done specifically to force a
  genuine OCR test).
- Only 3 real source documents exist in total, across 3 of the 15
  providers and 3 of the 4 product lines (no real travel-insurance IPID
  ingested yet) — the NLP/OCR real-document results should be read as an
  initial, genuine sample, not an exhaustive real-world benchmark.
- Automated regression test asserting language switch never changes
  recommendation scores (architecturally guaranteed and manually spot
  checked in this session, but not yet a standing test).
- See `docs/ACCESSIBILITY.md` for the accessibility review's own explicit
  scope and gaps (automated vs. manual checks), and the "E2E tests" section
  below for Playwright coverage and its own gaps.
- The automated suite intentionally uses the deterministic mock provider so
  tests never depend on a live key, quota, or network. A separate real
  `gemini-3.6-flash` integration run passed on 2026-08-29, including
  schema parsing plus German/English PostgreSQL-grounded Advisor questions;
  see `docs/RELEASE_CANDIDATE.md`. Lexical-only retrieval, regex-only PII
  redaction, and the absence of a Comparison Advisor UI remain disclosed
  limitations.

## How to reproduce this run

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download de_core_news_lg
alembic upgrade head
python -m scripts.seed
pytest -q
uvicorn app.main:app --reload --port 8000

cd frontend
npm install
npm run typecheck && npm run lint && npm test && npm run build
npm run dev
```

If `tesseract` is not on `PATH`, either add its install directory to `PATH`
yourself, or set `TESSERACT_CMD` in `backend/.env` to the full path of
`tesseract.exe`/`tesseract`.
