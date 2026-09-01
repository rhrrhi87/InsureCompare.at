# Implementation Plan — Gap Analysis & Roadmap

**Date:** 2026-08-27
**Scope:** Bring the existing InsureCompare.at prototype into line with the full
academic specification (bilingual EN/DE, explainable AI-assisted recommendation,
evidence traceability, admin catalogue management, testing, docs).

## 0. Repository provenance note

The working copy previously handed to this session (`Desktop\My Project`) turned
out to contain an unrelated Hotel Reservation System project. The real
InsureCompare.at codebase was located as `Downloads\insurecompare.tar.gz` and has
been extracted to **`Documents\insurance-system`**, which is now the project root
for all further work. A git repository has been initialised there.

The codebase found is **not a bare skeleton** — it is a working, well-structured
prototype with a real (non-fake) OCR/NLP pipeline, a real weighted-additive
recommender with SHAP-style contributions, working auth, and a working React SPA
covering the full core user journey. The gaps below are real gaps, not a
rewrite-from-scratch situation.

---

## 1. EXISTING

### Backend (FastAPI + SQLAlchemy 2.0 async + Alembic + PostgreSQL)
- Auth: register/login/refresh/me, JWT (HS256, 30 min access / 14 day refresh),
  bcrypt password hashing (`app/api/auth.py`, `app/core/security.py`).
- Domain models: `User`, `RiskProfile`, `Provider`, `Policy`, `Clause`,
  `Upload`, `Recommendation`, `AuditLog` (`app/db/models/*`).
- Enums: `UserRole`, `ProductLine` (car/household/travel/legal — matches
  in-scope Austrian product lines), `RiskLevel`, `RiskTolerance`,
  `CoverageLevel`, `DeductiblePreference`, `UploadStatus`, `ClauseType`
  (coverage/exclusion/limit/definition/other).
- Document pipeline (`app/nlp/ocr.py`, `app/nlp/extractor.py`): real
  pdfminer.six vector-text extraction with Tesseract OCR fallback (PSM 6,
  `deu` language pack, mean-confidence reporting), German regex-based numeric
  extraction (premium/deductible/coverage limit, German thousands format),
  spaCy sentence splitting with regex fallback, gBERT zero-shot clause
  classification with a deterministic keyword-based fallback, and a
  German→English controlled coverage/exclusion vocabulary. This is a genuine,
  transparent, testable pipeline — not fake AI.
- Recommender (`app/recommender/scorer.py`): weighted-additive 5-factor model
  — **Coverage 30% · Price 25% · Exclusion 20% · Fit 15% · Deductible 10%**,
  matching the specified model exactly. Per-feature contributions are exact
  Shapley values (documented rationale in `docs/architecture.md`). Produces a
  breakdown, per-factor contributions, and a template-generated narrative.
  Weight overrides supported end-to-end (`RiskProfile.weights` → API →
  `Recommender`).
- Services layer cleanly separates upload/compare/policy/profile/
  recommendation/admin/user concerns.
- `PolicyService` already has full CRUD for `Provider` and `Policy`
  (create/update/delete) — just not yet wired to admin API routes or UI.
- `AdminService.record_action()` (audit log writer) exists but is not called
  anywhere yet.
- Seed data (`backend/scripts/seed.py`): 6 real Austrian-market providers
  (UNIQA, Allianz Austria, Wiener Städtische, Generali Austria, Donau
  Versicherung, Helvetia Austria) and 12 policies across all four in-scope
  product lines — consistent with spec §10.
- Tests: `test_auth.py`, `test_recommender.py`, `test_nlp.py`,
  `test_recommendation_api.py` (22 tests total) using an in-memory SQLite
  fixture DB — real, meaningful assertions (weight normalisation, score
  bounds/ordering, extraction correctness, auth flows, 401/409 handling).
- Docker Compose stack: Postgres 16, Nginx TLS-terminating edge proxy +
  static-file web container, API container, one-shot seed service. CI
  workflow present (`.github/workflows/ci.yml`).
- `docs/architecture.md`, `docs/local-dev.md`, `docs/deployment.md` already
  exist and are accurate to the code.

### Frontend (React 18 + TypeScript + Vite + Tailwind + Zustand + TanStack Query)
- Full auth flow (login/register), Zustand store persisted to
  `localStorage` under `insurecompare.auth`.
- Pages: Home, Dashboard (risk-profile form), Upload (drag-and-drop, status
  badges, extraction summary), Compare (2–3 policy picker + side-by-side
  table, **3-policy cap already enforced** both client- and server-side),
  Recommendations (best-match hero card, ranked list, per-factor breakdown,
  narrative, "scoring methodology" card), Policy detail, Admin dashboard
  (KPIs, user list, audit feed, provider/policy distribution).
- Homepage already shows German terms alongside English category names
  (Kfz-Versicherung, Haushaltsversicherung, etc.) — a good seed for §7.
- Accessible-ish patterns already present: status conveyed via icon *and*
  text/colour (not colour alone) on upload/compare/policy pages.

---

## 2. MISSING (present in spec, absent in code)

1. **Bilingual EN/DE i18n — entirely absent.** No `react-i18next`, no locale
   files, no language switcher, all copy is hard-coded English JSX strings.
   This is the single largest gap (spec §4–§7, §24–§35, §40).
2. **Source provenance / evidence traceability model.** No fields for
   `source_url`, `source_organisation`, `retrieval_date`,
   `last_reviewed_date`, `document_language`, `extraction_method`,
   `document_title`, `document_type` on `Policy`/`Clause`. No
   "View source evidence" UI, no drill-down from
   recommendation → factor → clause → page → document (spec §9, §11, §19).
3. **Clause type coverage incomplete.** `ClauseType` has
   `COVERAGE/EXCLUSION/LIMIT/DEFINITION/OTHER`; spec §14 also requires
   `DEDUCTIBLE`, `OBLIGATION`, `TERRITORIAL_SCOPE`, `DURATION`,
   `OPTIONAL_BENEFIT`.
4. **Original-text vs normalised-concept separation is incomplete.**
   `Clause.text` holds the extracted sentence, but there is no explicit
   concept/label vs. original-clause architecture as required by §6/§35
   (original German clause must always be viewable unmodified regardless of
   UI language).
5. **"Beyond price comparison" / "Why InsureCompare" section** — not present
   on the homepage (spec §3, §26).
6. **"How it works" 4-step section** with the exact specified copy — not
   present (spec §25).
7. **Admin catalogue management UI** — only a read-only dashboard exists.
   No Providers/Policies/Documents/Audit as distinct admin nav sections, no
   create/edit/retire UI for providers or policies (spec §15, §32, §33),
   even though the backend service layer already supports CRUD.
8. **Admin API routes for provider/policy CRUD** — service methods exist
   (`PolicyService.create_policy` etc.) but `app/api/admin.py` does not
   expose them.
9. **Policy retirement/versioning semantics.** `Policy.is_active` exists but
   there's no `retired_at`, no supersede/version chain, and
   `PolicyService.delete_policy` performs a **hard delete** — spec §33/§36
   explicitly forbid destroying policy data needed to reproduce past
   recommendations.
10. **Audit logging is not wired up anywhere.** `AdminService.record_action`
    is dead code — no `LOGIN`, `UPLOAD_PROCESSED`,
    `RECOMMENDATION_GENERATED`, `POLICY_CREATED/UPDATED/RETIRED`,
    `WEIGHTS_CHANGED` events are ever written (spec §39).
11. **Advanced scoring-weight controls UI.** The model supports
    `RiskProfile.weights` end-to-end, but the dashboard has no
    hidden/collapsible weight-adjustment UI, and no "weights must sum to
    100%" client-side validation (spec §16, §28).
12. **Required-coverages selection UI.** `RiskProfile.required_coverages` is
    modelled and used by the scorer but never exposed as a UI field.
13. **Disclaimer text** (spec §47) is not shown anywhere in the app.
14. **"Demonstration premium" labelling** for unverified prices (spec §46) —
    all seed premiums are shown as if they were live figures, with no
    indication that this is prototype/demo data.
15. **Dedicated "Why this result" explanation page** with an explicit
    weight/sub-score/contribution table and evidence links per factor (spec
    §18, §19, §31) — the Recommendations page shows a breakdown and
    narrative but not the full tabulated contribution view or clause-level
    drill-down.
16. **Localisation testing, security testing beyond auth, performance
    scripts, accessibility audit** (spec §40, §41, §43, §44) — none exist
    yet.
17. **Extended docs set** (spec §49): `AI_PIPELINE.md`,
    `RECOMMENDATION_ENGINE.md`, `DATA_SOURCES.md`, `LOCALISATION.md`,
    `UI_DESIGN.md`, `DATABASE.md`, `TESTING.md`, `SECURITY.md`,
    `TRACEABILITY_MATRIX.md` do not exist (only architecture/local-dev/
    deployment do).
18. **Frontend component tests** — only 3 unit tests exist
    (`auth.test.ts`, `cn.test.ts`, `format.test.ts`); no component/page tests,
    no Playwright E2E despite `npx playwright test` being documented in the
    README.
19. **`.env.example` at repo root and per-package** exist, but no confirmed
    `SECRET`/`.env` hygiene check has been run yet against `.gitignore`
    (to be verified in Phase 13).

---

## 3. INCONSISTENT (present, but diverges from spec)

- **Hard delete on providers/policies** (`PolicyService.delete_provider`,
  `delete_policy`) contradicts the "never permanently delete" rule for
  reproducibility (§33). Must be replaced with retire/deactivate semantics
  before any admin UI is wired to it.
- **Frontend UI kit is a hand-rolled `Button`/`Card`/`Badge` set, not
  shadcn/ui** as the spec's recommended stack states. Per spec §22 ("do not
  replace working frontend architecture without a compelling reason") this
  is **not** being changed — it is close enough in spirit (Tailwind-based,
  accessible-ish, consistent) and a wholesale swap would be high-risk,
  low-value churn this late in the project. Documented here as a deliberate,
  reasoned deviation rather than an oversight.
- **Homepage hero copy / structure** does not match the spec's exact
  EN/DE strings (§24) — will be rewritten as part of the i18n pass since the
  copy has to be re-authored as translation keys anyway.
- **`shap` is a pinned dependency** (`requirements.txt`) but is not actually
  imported anywhere; the scorer computes exact Shapley values analytically
  (correctly, since the model is linear/additive) instead. Not a functional
  bug — the docstring in `scorer.py` explains why — but the unused
  dependency should either be removed or the docstring's justification
  linked from `docs/RECOMMENDATION_ENGINE.md` so a viva examiner isn't
  confused about why `shap` is imported nowhere.

---

## 4. TO PRESERVE (do not rewrite)

- The five-factor weighted-additive recommender and its exact default
  weights.
- The OCR → NLP extraction pipeline design (vector-PDF-first, OCR fallback,
  keyword-fallback classifier) — this is the core research contribution and
  is already implemented honestly (no fabricated confidence values).
- The existing route structure, service-layer separation, and Pydantic
  schema boundaries.
- The existing product line scope (car/household/travel/legal) and provider
  catalogue.
- The existing Docker/Nginx/Compose deployment topology.
- The existing test fixtures and test style (in-memory SQLite, httpx
  `AsyncClient`) — new tests will follow the same pattern.
- The custom Tailwind UI kit (see Inconsistent, above) — refined, not
  replaced.

## 5. TO IMPLEMENT (phase-ordered — see §6 of this doc)

See the phase list below; in priority order the largest blocks of new work
are: i18n architecture + full translation coverage, source-provenance data
model + evidence UI, admin catalogue CRUD UI + wiring, audit-log wiring,
policy retirement semantics, disclaimer + demonstration-data labelling,
advanced scoring UI, and the extended docs set.

## 6. TO TEST

- Localisation tests (EN renders English, DE renders German, switch
  persists across refresh/login, score is language-invariant).
- Admin CRUD authorization tests (non-admin blocked from provider/policy
  mutation and audit endpoints).
- Upload/document endpoint tests (currently untested despite being a core
  feature).
- Audit log tests (once wired: each listed action type actually appears).
- Policy retirement tests (retired policy excluded from new recommendations
  but still referenced by historical `Recommendation.ranked_policies`
  snapshots).
- Frontend component tests for the language switcher, evidence viewer, and
  admin catalogue screens.

---

## 7. Cross-check against the original design doc & dissertation

Read from `InsureCompare_System_and_UI_Design Amr Darwish.docx` and
`InsureCompare_Dissertation_FINAL.docx` (Downloads) to confirm the code stays
consistent with what was already submitted academically:

- **Scoring weights confirmed exact**: Coverage 30% · Price 25% ·
  Exclusions 20% · Profile Fit 15% · Deductible 10%, sourced partly from a
  small informal ranking exercise and partly from published VKI (Austrian
  consumer association) guidance. No change needed — code already matches.
- **DB design specifies one additional entity not yet in the code:
  `sessions`** (refresh-token rotation: id, user_id, refresh_token,
  expires_at, revoked). The current backend uses fully stateless JWT refresh
  with no persistence/revocation. This is a real gap against the frozen
  design and against spec §36/§38 ("session handling where existing design
  requires"). **Added to Phase 3 (auth review) below.**
- The design doc's `clauses` table also carries a nullable `upload_id` FK
  (distinguishing catalogue-seeded clauses from user-upload-extracted
  clauses) — folded into the Phase 4 provenance-model work already planned.
- **A `Database Structure...png` found alongside the docs is a superseded
  early draft** (different entities entirely — `INSURANCE_OFFERS`,
  `CLIENTS`, `SEARCH_HISTORY`, `ERROR_LOGS`, `AIConfidenceScore`, etc.). It
  is **not** the authoritative schema and must not be used as a reference —
  the design doc + dissertation (which agree with each other) are
  authoritative.
- **Competitor framing guidance**: the dissertation compares against
  Durchblicker, Check24 Austria and Versicherungen.at on capability
  dimensions (coverage analysis, exclusion extraction, explainability, OCR
  upload, personalisation, auditability) but is explicit that InsureCompare
  does **not** compete on scale, insurer integrations, or live pricing, and
  is advisory-only. Any "Why InsureCompare" copy must keep this framing —
  "different proposition" / explainability-and-coverage-aware niche — never
  "better than X" on price or scale, and never name competitors in
  public-facing marketing copy (only in academic docs, matching the
  original spec instruction already followed in this plan).
- **The dissertation records English-only UI as a stated limitation /
  future work.** Implementing full EN/DE bilingual support now (this
  session's Phase 2) directly closes that previously-documented gap — it is
  not a deviation from the frozen design, it is completing declared future
  work.
- The dissertation reports specific evaluation numbers from its own prior
  academic evaluation (NLP F1, P95 latency, SUS trust scores, expert
  agreement %). These are **prior reported results, not something this
  session has measured**. Per spec §41/§43, this session must not restate
  them as freshly-measured claims; where referenced in docs they will be
  cited as "as reported in the dissertation evaluation" and kept separate
  from any new scripts/results this session actually produces and runs.

---

## Phase order (per project instructions)

1. ✅ Repository audit and gap analysis (this document)
2. Design system + bilingual i18n foundation
3. Auth/roles review (mostly done — add the `sessions` table for
   refresh-token rotation/revocation per the frozen design doc; otherwise
   verify only)
4. Insurance domain + provider catalogue (source provenance model, clause
   type expansion, admin CRUD wiring, retirement semantics)
5. Document processing / OCR / NLP (extend clause types, wire evidence
   fields through)
6. Risk profile (advanced weight UI, required-coverages UI)
7. Explainable recommendation engine ("Why this result" page, evidence
   drill-down)
8. Three-policy comparison (already compliant — verify only)
9. Evidence and source traceability (cross-cutting; builds on Phase 4/5)
10. Consumer UI (homepage "Beyond price" + "How it works" + disclaimer)
11. Admin UI (Providers/Policies/Documents/Audit screens)
12. Automated testing (backend + frontend + localisation)
13. Performance, security and accessibility review
14. Documentation and README refresh
15. Final acceptance audit against the checklist in the project spec §54

Each phase ends with build + lint + test before moving to the next, per
project instructions.

---

## Session status (2026-08-27)

**Environment constraint**: this session had no Node.js, Python, or Docker
available, so "build + lint + test before moving to the next phase" was
done as careful manual/static review (including one dedicated static-review
subagent pass that caught and fixed 3 real issues: an unused import, a
TypeScript union-type inference bug, and a wrong i18n key) rather than
actual `tsc`/`pytest`/`vite build` execution. **This must be verified for
real before the project is considered done** — see `docs/TESTING.md`.

**Completed this session** (Phases 2, 4, 6, 9, 10, 11 substantially; 14 in
full; 12/13 partially — tests written but not run):

- Bilingual EN/DE i18n across every existing page + all new pages
  (`docs/LOCALISATION.md`).
- Source-provenance model (`Policy`/`Clause` provenance fields,
  `is_demo_data` honesty flag), expanded `ClauseType` taxonomy, `sessions`
  table for refresh-token rotation/revocation, migration `0002_*`.
- Policy/provider retire-not-delete semantics + admin UI
  (`AdminProvidersPage`, `AdminPoliciesPage`, `AdminDocumentsPage`,
  `AdminAuditPage`, `AdminLayout` tab nav).
- Audit logging actually wired up (`LOGIN`, `UPLOAD_PROCESSED`,
  `RECOMMENDATION_GENERATED`, `POLICY_CREATED/UPDATED/RETIRED`,
  `WEIGHTS_CHANGED`) — was previously dead code.
- Evidence-traceability UI: `PolicyDetailPage` Source Evidence section,
  richer per-clause display on `UploadPage`, `/policies/{id}/clauses`
  endpoint.
- Dashboard: collapsible advanced scoring-weights panel (validated to sum
  to 100%) and a required-coverages picker.
- Homepage: "Beyond price comparison" differentiation matrix, "How it
  works" 4-step section, About section, disclaimer in both footers —
  cross-checked against the dissertation's careful competitor-framing
  language (never naming Durchblicker/Check24 in marketing copy).
- New docs: `AI_PIPELINE.md`, `RECOMMENDATION_ENGINE.md`,
  `DATA_SOURCES.md`, `LOCALISATION.md`, `UI_DESIGN.md`, `DATABASE.md`,
  `SECURITY.md`, `TESTING.md`, `TRACEABILITY_MATRIX.md`; README and
  `architecture.md` refreshed.
- New backend tests: clause-type classification, refresh-token rotation,
  logout revocation, policy retire/reactivate, audit-event coverage.

**Still open** (see `docs/TESTING.md` "Not yet covered" for the honest
list): actually running the full build/lint/test suite; upload-endpoint
integration tests; frontend component tests for the new admin/evidence
UI; a WCAG accessibility audit; a performance benchmark script;
server-side (not just localStorage) language persistence; error-code-based
backend i18n beyond the current golden-path string-matching table.

---

## Session status (2026-08-28) — Run / Test / Debug / Verify

The environment constraint above is **resolved**: Python, Node, PostgreSQL
(installed natively via winget after Docker Desktop turned out to be
non-functional — WSL2 was not installed on this machine, and enabling it
requires a system-feature change + reboot this session correctly declined
to make unilaterally; the user chose the native-Postgres path instead —
see the full account in this session's transcript) and Tesseract OCR were
all verified and used for real. Every claim in `docs/TESTING.md` above this
point was rewritten to describe an **actually executed** run, replacing the
earlier honesty disclaimer.

**13 real defects found and fixed** by actually running the stack instead
of only reading the code — full detail and fixes in `docs/TESTING.md`:

1. `aiosqlite` missing from `requirements.txt` (pytest couldn't collect).
2. `create_async_engine` passed Postgres-only pool kwargs unconditionally;
   crashed against SQLite.
3. `SessionService.get_active` crashed comparing an aware vs. naive
   datetime (SQLite quirk).
4. JWTs had no `jti`; two tokens issued in the same second were identical,
   defeating refresh-token single-use rotation — a real security-relevant
   bug, not just a test flake.
5. Alembic migrations used `sa.Enum(..., create_type=False)`, but
   `create_type` isn't a parameter of the generic `sqlalchemy.Enum` — it's
   silently dropped and reset to `True` on PostgreSQL-dialect adaptation.
   Every enum column's `CREATE TYPE` ran twice and failed against real
   Postgres (SQLite has no equivalent check, so this was invisible before).
6. Migration `0002`'s revision id exceeded Alembic's 32-char
   `version_num` column, corrupting the migration transaction after all its
   DDL had already executed.
7. `scripts.seed`'s success-path logging crashed on Windows (see #9).
8. **Most significant data-correctness bug**: every `Enum(PythonEnum)`
   column defaulted to storing the member *name* (`"CAR"`) instead of its
   *value* (`"car"`), which is what the Postgres enum types (and the whole
   JSON API contract) actually use — 100% of writes against real Postgres
   failed. Invisible under SQLite. Fixed with a shared `str_enum()` helper
   applied to all 9 enum columns.
9. Windows console defaults to `cp1252`; logging any German text (ä/ö/ü/ß)
   from inside an exception handler crashed with a second, unrelated
   `UnicodeEncodeError`, turning recoverable errors into 500s app-wide.
10. **Most significant AI-pipeline bug**: `GBERT_MODEL` defaulted to
    `deepset/gbert-base`, which has no NLI/entailment head — every clause,
    regardless of content, was classified identically once
    `transformers`/`torch` were actually installed and exercised (the unit
    tests only ever exercised the keyword fallback, by design, so this was
    invisible to them). This directly undermined the project's core
    "AI-assisted clause classification" claim. Fixed by switching to
    `Sahajtomar/German_Zeroshot`, an actually NLI-fine-tuned German model.
11. Tesseract wasn't on `PATH` on this Windows machine (a common failure
    mode of the official installer) and the app had no fallback — fixed
    with a `TESSERACT_CMD` setting plus Windows-path auto-detection.
12. Two admin-provider-form buttons both rendered the literal label
    "New Provider", made ambiguous by sharing one translation key.
13. `UploadPage` displayed the wrong number for "OCR confidence" — the
    first clause's NLP classification confidence, not the real
    `upload.ocr_confidence` field.

**Fully manually verified through the real browser + real Postgres-backed
API** (see `docs/TESTING.md` for the per-item table): landing page, EN/DE
switching, registration, login, logout (with real server-side session
revocation confirmed over the network), user dashboard, risk-profile
preferences including the advanced-weights panel and required-coverages
picker, policy catalogue, 3-policy comparison, policy detail, source
evidence (honest empty state for demo data), document upload, OCR against
a real German test image (94% confidence), NLP extraction, recommendation
generation, the explainable score breakdown, admin login, provider
management (list + live create), policy management, policy retirement
(verified persisted via the API, then reversed), the admin documents page,
and the audit log (real entries).

**Still open** (unchanged from the list above, now confirmed still
accurate rather than assumed): literal OS-level file-picker upload
automation (the upload endpoint itself was fully exercised instead), and a
standing automated test asserting language switches never change scores.
Playwright E2E, an accessibility review, and an NLP precision/recall
benchmark were completed in the academic data-quality phase below.

## Academic data-quality phase (2026-08-28)

A second, distinct pass focused on data honesty and measurement rather
than functional bugs. Full detail lives in dedicated docs; this is a
pointer, not a duplicate:

- **Provider catalogue expanded from 6 to 15 real Austrian insurers**,
  each with a real, verified, own-domain `logo_url` (never a generated or
  recreated logo) and a uniform, explicitly-placeholder `rating_score`
  (the previous catalogue's *differentiated* per-provider ratings were
  themselves fabricated and have been corrected). See
  `docs/DATA_SOURCES.md` and `docs/DATA_PROVENANCE_AUDIT.md`.
- **Full data provenance audit** of every provider/policy/clause record
  currently in the database, classified `VERIFIED_SOURCE` /
  `DOCUMENT_EXTRACTED` / `DERIVED` / `DEMO_SYNTHETIC` / `UNKNOWN` — see
  `docs/DATA_PROVENANCE_AUDIT.md`. No `VERIFIED_SOURCE` records exist yet,
  and the document says so plainly rather than implying otherwise.
- **Real, measured NLP/OCR evaluation** against controlled test fixtures
  (`backend/scripts/evaluate_nlp.py`, `docs/NLP_EVALUATION.md`) —
  including the honestly weak 40% zero-shot classification accuracy,
  reported without softening.
- **Accessibility review**: automated axe-core scan of 9 pages (0
  violations after fixing 6 real, disclosed defects — see
  `docs/ACCESSIBILITY.md`) plus manual code-level checks. Not a WCAG 2.1
  AA compliance claim.
- **Playwright E2E suite added** (`frontend/e2e/`): 8 named user journeys
  plus the accessibility scan, both passing in full against the real
  running application. Not present before this phase.

## Final release-candidate freeze (2026-08-28) and AI Policy Advisor (2026-08-29)

Two further passes, after the real-document phase above:

**Freeze pass**: removed the "academic research prototype" framing from
normal user-facing UI (footer, homepage About section — replaced with a
plain tagline and a new `/legal` page), added a restrained "Demonstration
data" badge to the Compare and Recommendations pages (previously only
Policy Detail/Admin showed it), reviewed and confirmed the real-document
redistribution boundary (PDFs excluded from git, manifest + checksums +
download script kept — see `docs/DATA_PROVENANCE_AUDIT.md` §8), removed 13
disposable QA-test upload rows from the dev database, and produced
`docs/RELEASE_CANDIDATE.md`.

**AI Policy Advisor**: integrated Google Gemini (`gemini-3.6-flash` via
the official `google-genai` SDK) as an evidence-grounded RAG explanation
layer added *after* the existing OCR/NLP pipeline — added, not
substituted. Retrieval is scoped per-document (never cross-document),
evidence IDs returned by the LLM are always re-validated against
PostgreSQL before rendering, and a fixed "cannot be confirmed" response is
returned — without even calling the LLM — whenever no clause is
lexically relevant to a question. A deterministic mock provider
(`LLM_PROVIDER=mock`, the default) is used for all 25 new backend tests
and both new Playwright E2E tests, so the test suite never depends on a
live API key. Full design in `docs/AI_ADVISOR_ARCHITECTURE.md`; the
existing deterministic recommendation engine, OCR/NLP pipeline, and
provider catalogue/logos are unchanged.
