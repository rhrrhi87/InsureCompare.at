# InsureCompare.at

AI-assisted, coverage-aware and explainable platform for comparing Austrian
retail insurance policies on price, coverage, exclusions, deductibles and
profile fit — not price alone. Built as the prototype for the SWE6010 BEng
Software Engineering dissertation at the University of Greater Manchester.

The core research contribution: public insurance documents → OCR/NLP
extraction → structured, evidence-linked insurance knowledge → a
weighted-additive, fully explainable recommendation, with every factor
traceable back to the original clause and page it came from. See
`docs/RECOMMENDATION_ENGINE.md` and `docs/AI_PIPELINE.md`.

## Academic motivation and research problem

Price-only comparison can make policies with materially different coverage,
deductibles, limits, exclusions, and obligations appear interchangeable. In
the Austrian market, these details are spread across insurer product pages,
Insurance Product Information Documents (IPIDs), and policy wording, making a
transparent like-for-like comparison difficult.

InsureCompare.at investigates whether a software system can combine structured
policy attributes with document-assisted extraction to rank policies by both
cost and coverage fit, while exposing the inputs, weights, source evidence,
and limitations behind every result. It is a research prototype, not a live
quotation service or a substitute for professional insurance advice.

## Key features

- Coverage-aware comparison across premium, deductible, coverage breadth,
  exclusions, provider rating, and user-defined priorities.
- Explainable recommendations with per-factor weights, sub-scores, and a
  reproducible weighted-additive total.
- PDF/image ingestion with text extraction, OCR fallback, numeric-field
  extraction, insurance vocabulary matching, and clause classification.
- Evidence-linked policy Q&A that returns the supporting extracted clauses and
  refuses unsupported conclusions.
- Bilingual English/German interface, role-based user/admin workflows,
  provenance labels, audit logging, and policy retirement rather than deletion.

## AI/NLP and explainability scope

The document pipeline tries embedded PDF text first and Tesseract OCR second.
It then applies deterministic patterns and insurance vocabulary matching plus
either a German zero-shot classifier or a keyword fallback. Measured accuracy
is reported in `docs/NLP_EVALUATION.md`; neither classifier is presented as
production-ready.

Recommendation explainability is implemented directly as a weighted-additive
model, not as post-hoc SHAP/LIME output. Each displayed factor records its
configured weight, normalized sub-score, contribution, and human-readable
rationale. The optional Gemini-backed Policy Advisor is evidence-grounded;
automated tests use the deterministic mock provider and require no API key.

## System architecture

```text
React/Vite SPA
      │ HTTPS / JSON
      ▼
Nginx reverse proxy ──► FastAPI services ──► PostgreSQL
                              │
                              ├─► recommendation scorer + explainer
                              ├─► PDF text extraction / Tesseract OCR / NLP
                              └─► evidence retrieval / optional LLM provider
```

See `docs/architecture.md`, `docs/AI_PIPELINE.md`,
`docs/AI_ADVISOR_ARCHITECTURE.md`, and `docs/DATABASE.md` for the detailed
component, data-flow, security, and schema descriptions.

After a document is processed, the **AI Policy Advisor** (KI-Versicherungsberater)
lets you ask questions about it in plain language — "Is theft covered?",
"What's my deductible?" — and answers only from that document's own
extracted clauses, never from generic insurance knowledge, with the
original source clause always shown underneath. See
`docs/AI_ADVISOR_ARCHITECTURE.md`.

## Research claim boundary — read this before anything else

Real official Austrian insurer documents (3 IPIDs from UNIQA, Generali,
and Wiener Städtische — see `docs/DATA_PROVENANCE_AUDIT.md` §4a and
`backend/data/source_documents/MANIFEST.json`) were used to validate:
document ingestion, PDF text extraction, OCR, clause extraction, clause
classification, and evidence traceability, end to end, against genuine
source material.

**The comparison/recommendation catalogue still contains `DEMO_SYNTHETIC`
policy and pricing records** where equivalent official comparable pricing
was unavailable — real IPIDs are legally standardized documents that do
not disclose an exact premium or sum insured (those are set per contract).

**Do not describe this project as one where** "recommendations are based
entirely on live/real insurer quotations" **or where** "InsureCompare
currently compares live Austrian insurance prices" — neither is accurate.
The correct framing: *the prototype evaluates document understanding on
real official Austrian insurance documents, while controlled synthetic
policy and pricing data is used for parts of the comparison and
recommendation demonstration where authoritative comparable pricing is
unavailable.* See `docs/RELEASE_CANDIDATE.md` for the full scope split.

The UI is fully bilingual (English default, German/Austrian terminology as
a complete second localisation) — see `docs/LOCALISATION.md`.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend  | FastAPI (Python 3.12) + SQLAlchemy 2.0 (async) + Alembic |
| Database | PostgreSQL 16 |
| NLP      | spaCy (`de_core_news_lg`) + zero-shot classification (`Sahajtomar/German_Zeroshot`) + a keyword/regex fallback classifier — see `docs/NLP_EVALUATION.md` for how these compare |
| OCR      | Tesseract 5 (`deu` language pack) + pdfminer.six (vector-PDF text extraction is tried first; OCR is a fallback) |
| ML/XAI   | scikit-learn (evaluation metrics) + an additive, per-factor-weighted explainer (not a SHAP library) |
| AI Policy Advisor | Optional Google Gemini model via `google-genai`, evidence-grounded RAG — see `docs/AI_ADVISOR_ARCHITECTURE.md`; a deterministic mock provider is used for all automated tests |
| Reverse proxy | Nginx 1.25 |
| Container runtime | Docker + Docker Compose v2 |

## Installation requirements

- Python 3.11 or newer (the backend container uses Python 3.12)
- Node.js 20 and npm
- PostgreSQL 16
- Tesseract 5 with the German (`deu`) language pack
- Docker Desktop with Compose v2, if using the containerized path

## Quickstart with Docker Compose

```bash
git clone https://github.com/rhrrhi87/InsureCompare.at.git
cd InsureCompare.at
cp .env.example .env       # then edit secrets
docker compose up --build  # ~90s on a 4 vCPU VM
```

The Docker path has not been run end-to-end in this project's own test
sessions (Docker Desktop was present but WSL2 wasn't available in the
environment used) — it is provided as-is and should be verified on your
own machine. **The fully-verified path is native, without Docker** — see the
backend/frontend setup below and `docs/local-dev.md`.

The frontend lands on https://localhost (Docker) or http://localhost:5173
(native dev server). Demo accounts:

- User: `user@test.at` / `user123`
- Admin: `admin@insurance.at` / `admin123`

## Repository layout

```
insurecompare/
├── backend/                  FastAPI app
│   ├── app/
│   │   ├── api/              Route modules
│   │   ├── core/             Config, security, logging
│   │   ├── db/               SQLAlchemy models, session, seeders
│   │   ├── nlp/              OCR + NLP pipeline
│   │   ├── recommender/      Scoring engine + additive explainer
│   │   ├── schemas/          Pydantic v2 schemas
│   │   └── services/         Application services
│   ├── alembic/              Migrations
│   ├── scripts/              Seed + admin scripts
│   └── tests/                pytest suites
├── frontend/                 React 18 + TypeScript SPA
│   ├── public/
│   └── src/
│       ├── api/              API client + types
│       ├── components/       Reusable UI + layouts (incl. admin tab nav)
│       ├── features/         Auth, upload, dashboard, recommendations,
│       │                     policy detail, admin (providers/policies/
│       │                     documents/audit) …
│       ├── i18n/             react-i18next configuration
│       ├── lib/              Helpers, query client, i18n domain helpers
│       ├── locales/          en/ + de/ translation namespaces
│       ├── pages/            Route pages
│       ├── routes/           Route table
│       ├── stores/           Zustand stores
│       └── styles/           Tailwind globals
├── nginx/                    Reverse-proxy config
├── docker/                   Service-specific Dockerfiles
├── docs/                     Architecture, deployment, ADRs
└── .github/workflows/        CI pipelines
```

## Environment configuration

Copy `.env.example` to `.env` and replace every security-sensitive placeholder
before starting the stack. At minimum configure `POSTGRES_PASSWORD`,
`DATABASE_URL`, and a random 32-byte-or-longer `JWT_SECRET`. Leave
`LLM_PROVIDER=mock` and `GEMINI_API_KEY` empty for a fully local setup; only set
the key in an untracked local `.env` when explicitly enabling Gemini. Vite
exposes only variables prefixed with `VITE_`, so secrets must never be placed
in frontend environment variables.

All `.env` variants are ignored except committed `.env.example` templates.
See `.env.example`, `docs/SECURITY.md`, and `docs/deployment.md` for the complete
variable reference and production guidance.

## PostgreSQL and database migrations

For a local PostgreSQL 16 server, create an empty database and application user
matching `DATABASE_URL`. Alternatively, start only the database service with
`docker compose up -d db`. From `backend/`, apply the versioned Alembic schema
and load the clearly labelled demonstration catalogue:

```bash
alembic upgrade head
python -m scripts.seed
```

Migration files live in `backend/alembic/versions/`; schema rationale and the
PostgreSQL-specific enum behavior are documented in `docs/DATABASE.md`.

## Backend setup

This is the fully-verified path (see `docs/TESTING.md`). Full detail in
`docs/local-dev.md`; short version:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download de_core_news_lg
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload --port 8000
```

The API and OpenAPI UI are available at `http://localhost:8000` and
`http://localhost:8000/docs`.

## Frontend setup

```bash
cd frontend
npm ci
npm run dev
```

The Vite application runs at `http://localhost:5173` and proxies `/api` to the
backend. Run the backend and frontend in separate terminals.

To also reproduce the real-document evaluation (optional — the app runs
fully without it):

```bash
cd backend
python -m scripts.download_source_documents   # re-downloads the 3 real IPIDs
python -m scripts.ingest_real_documents        # requires the backend dev server running
python -m scripts.evaluate_nlp                 # writes scripts/nlp_evaluation_results.json
```

## Testing and evaluation

```bash
cd backend && pytest -q                 # backend unit + integration tests
cd frontend && npm run typecheck        # TypeScript project checks
cd frontend && npm run lint             # ESLint
cd frontend && npm test                 # Vitest unit tests
cd frontend && npm run build            # production frontend build
cd frontend && npm run e2e              # Playwright E2E + axe-core; both servers required
cd backend && python -m scripts.evaluate_nlp      # NLP/OCR evaluation
cd backend && python -m scripts.evaluate_advisor  # advisor evaluation (mock by default)
```

The Playwright suite includes user/admin journeys and an axe-core accessibility
scan. It requires seeded PostgreSQL data plus the backend and frontend dev
servers. See `docs/TESTING.md`, `docs/ACCESSIBILITY.md`, and
`docs/NLP_EVALUATION.md` for prerequisites, datasets, measured results, and
explicit coverage gaps.

## Data provenance

The repository deliberately distinguishes:

- `VERIFIED_SOURCE`: provider facts supported by an official source.
- `DOCUMENT_EXTRACTED`: clauses extracted from a referenced source document.
- `DERIVED`: values computed from other recorded information.
- `DEMO_SYNTHETIC`: controlled demonstration policy/pricing data.

Official insurer PDFs are referenced by URL, checksum, and retrieval metadata
in `backend/data/source_documents/MANIFEST.json`; they are not redistributed.
Document-extracted evaluation fixtures and synthetic catalogue records are not
represented as verified live policy data. See `docs/DATA_SOURCES.md` and
`docs/DATA_PROVENANCE_AUDIT.md` for the record-level audit.

## Documentation

- `docs/RELEASE_CANDIDATE.md` — current release status, scope split, and academic claim boundaries (start here)
- `docs/AI_ADVISOR_ARCHITECTURE.md` — the AI Policy Advisor: RAG, evidence grounding, anti-hallucination design, PII/prompt-injection handling, Gemini configuration
- `docs/IMPLEMENTATION_PLAN.md` — gap analysis and phase plan
- `docs/architecture.md` — system architecture
- `docs/AI_PIPELINE.md` — OCR/NLP document processing pipeline
- `docs/RECOMMENDATION_ENGINE.md` — the explainable scoring model
- `docs/DATA_SOURCES.md` — provenance policy, demo-vs-real data
- `docs/DATA_PROVENANCE_AUDIT.md` — per-record classification of every provider/policy/document/clause (`VERIFIED_SOURCE` / `DOCUMENT_EXTRACTED` / `DERIVED` / `DEMO_SYNTHETIC`)
- `docs/NLP_EVALUATION.md` — measured clause-classification and OCR accuracy, on both synthetic and real documents
- `docs/ACCESSIBILITY.md` — automated (axe-core) + manual accessibility review
- `docs/LOCALISATION.md` — the EN/DE i18n architecture
- `docs/UI_DESIGN.md` — screens, design decisions
- `docs/DATABASE.md` — schema and design rationale
- `docs/SECURITY.md` — auth, sessions, authorization, known limitations
- `docs/TESTING.md` — test coverage and how to run it, including E2E
- `docs/TRACEABILITY_MATRIX.md` — requirement → implementation → test
- `docs/local-dev.md` / `docs/deployment.md` — running the stack

## Limitations

- The comparison/recommendation catalogue is `DEMO_SYNTHETIC` (12 policies,
  9 of 15 providers with no product at all) — see the research claim
  boundary above and `docs/DATA_SOURCES.md`.
- Only 3 real source documents exist, across 3 of the 15 providers and 3
  of the 4 product lines (car, household, legal — no real travel IPID
  yet) — the real-document NLP/OCR results are an initial genuine sample,
  not an exhaustive benchmark. See `docs/NLP_EVALUATION.md`.
- Neither clause classifier is production-ready: measured real-document
  accuracy is 55.9% (keyword fallback) and 32.2% (zero-shot gBERT) —
  see `docs/NLP_EVALUATION.md` for full per-class results and why.
- OCR character recognition is strong (92.6% confidence on a real
  document) but reading order breaks down on multi-column real layouts —
  a disclosed, explained limitation, not a hidden one.
- No screen-reader (JAWS/NVDA/VoiceOver) pass has been done; the
  accessibility review is automated (axe-core, 0 violations across 9
  pages) plus manual code-level checks — see `docs/ACCESSIBILITY.md`.
- Backend error messages are localised for the common golden-path errors
  only, not exhaustively — see `docs/LOCALISATION.md`.
- Preferred language persists in the browser only, not on the user's
  server-side profile — see `docs/LOCALISATION.md`.
- The AI Policy Advisor's retrieval is lexical (keyword overlap), not
  semantic — a question asked in a different language than the uploaded
  document's text will not match even when a human would see the
  connection; no pgvector/embedding search is used. PII redaction is
  regex-based and will not catch a bare personal name. See
  `docs/AI_ADVISOR_ARCHITECTURE.md` for the full list.

## Future work

- Ingest more real source documents — more insurers, all 4 product lines,
  and full policy wording (AVB) alongside IPIDs — to widen the real-data
  NLP/OCR evaluation sample.
- Fine-tune a German clause classifier on real labelled data once enough
  exists; in the meantime, prefer the keyword classifier over zero-shot
  (it measurably outperforms it on both synthetic and real data).
- Layout-aware OCR (column detection) instead of single-block PSM 6, to
  fix the real multi-column reading-order finding in `docs/NLP_EVALUATION.md`.
- Persist preferred language on the user profile for cross-device sync.
- Error-code-based backend i18n instead of the current string-matching
  fallback table.
- A screen-reader pass and WCAG 2.1 AA contrast audit beyond axe-core's
  automated coverage.

## Academic-use notice and disclaimer

InsureCompare.at is an academic research prototype. It does not provide
binding insurance quotations or regulated financial advice. Product
information must be verified against the insurer's current official
documentation. It does not compare live Austrian insurance prices, and its
recommendations are not based on live/real insurer quotations — see the
research claim boundary at the top of this file.

## License

Academic prototype. The 3 real source documents used to evaluate document
understanding (`backend/data/source_documents/MANIFEST.json`) are publicly
available Austrian IPIDs, published under the Insurance Distribution
Directive (Directive (EU) 2016/97) — they are referenced by official URL
and checksum, not redistributed in this repository (see
`docs/DATA_PROVENANCE_AUDIT.md` §8). The demonstration catalogue's policy
and pricing content is synthetic, not extracted from any real document.
