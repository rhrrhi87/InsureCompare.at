# Architecture

InsureCompare.at follows a classical three-tier separation between
presentation (React 18 SPA), application (FastAPI), and data (PostgreSQL),
with the AI services packaged inside the application tier.

## Tiers

```
            ┌───────────────────────────────────────────────────────┐
            │   Presentation Tier                                   │
            │   React 18 + TypeScript + Tailwind CSS + Zustand      │
            │   Served as static files by Nginx (`web` container)   │
            └───────────────────────────▲───────────────────────────┘
                                        │ HTTPS  (TLS via edge proxy)
            ┌───────────────────────────▼───────────────────────────┐
            │   Edge reverse proxy (`proxy` container)              │
            │   Nginx with TLS termination + routing                │
            └───────────────────────────▲───────────────────────────┘
                                        │ HTTP
            ┌───────────────────────────▼───────────────────────────┐
            │   Application Tier                                    │
            │   FastAPI (async Python 3.11)                         │
            │   ┌──────────┬──────────────┬───────────┬───────────┐ │
            │   │ Auth     │ Upload + NLP │ Recommender│ Admin    │ │
            │   └──────────┴──────────────┴───────────┴───────────┘ │
            │   spaCy + gBERT + Tesseract OCR + SHAP-style scorer   │
            └───────────────────────────▲───────────────────────────┘
                                        │ asyncpg
            ┌───────────────────────────▼───────────────────────────┐
            │   Data Tier                                           │
            │   PostgreSQL 16 (+ optional pgvector)                 │
            │   users • sessions • risk_profiles • providers        │
            │   policies • clauses • uploads • recommendations      │
            │   audit_logs                                          │
            └───────────────────────────────────────────────────────┘
```

## Presentation-layer localisation

The React SPA is fully bilingual (English default, German — Austrian
terminology — as a complete second localisation) via `react-i18next`. The
API and database are language-independent: they store/return stable
concept identifiers, never UI copy, so switching language is a pure
frontend concern that never touches scored/ranked data. See
`docs/LOCALISATION.md`.

## Request paths

- **Browser → Edge proxy → Web container** for `/` and static assets.
- **Browser → Edge proxy → API container** for `/api/*`, `/docs`, `/openapi.json`.
- **API → DB** for everything else.

## Authentication

- JWT (HS256 by default, configurable to RS256) for both access and
  refresh tokens.
- 30-minute access token. 14-day refresh token, additionally backed by a
  `sessions` table row so it can actually be revoked (rotation-on-use and
  explicit logout both work by revoking the matching session) — see
  `docs/SECURITY.md`.
- bcrypt(12) password hashing; constant-time comparison.

## NLP pipeline (per upload)

1. **Upload validation** — MIME allowlist + 10 MB size cap.
2. **Vector-PDF extraction** — pdfminer.six. If >50 tokens come out, OCR is
   skipped (factor-of-five latency win on most IPIDs).
3. **OCR fallback** — Tesseract with `lang=deu` and PSM 6, plus mean
   confidence reported for downstream warnings.
4. **Normalisation** — soft-hyphen removal, line-break dehyphenation, NBSP
   normalisation.
5. **Sentence splitting** — spaCy `de_core_news_lg` when available, regex
   fallback otherwise (handles `z.B.`, `bzw.`, `Art.`, `Nr.`).
6. **Numeric extraction** — premium / deductible / coverage limit via
   compiled regex against the German amount format.
7. **Clause classification** — gBERT zero-shot when available; keyword-based
   fallback in deterministic environments.
8. **Coverage / exclusion mapping** — controlled vocabulary lookup for known
   German→English mappings (Diebstahl → Theft, etc.).

## Recommendation scoring

Linear additive function with five weighted features:

```
S(p, u) = 0.25·f_price + 0.30·f_coverage + 0.20·f_exclusion
        + 0.10·f_deductible + 0.15·f_fit
```

The contribution of each feature is itself the exact Shapley value (additive
linear models satisfy SHAP's symmetry + dummy axioms), so the explanation
panel returns the same numbers without invoking TreeSHAP.

## Where state lives

- **Postgres**: all canonical state.
- **Frontend Zustand**: access token, refresh token, current user.
- **React Query**: server state cache (policies, providers, audit log…).
- **Browser localStorage**: persisted Zustand store under `insurecompare.auth`.

No state lives in the API process between requests; horizontal scaling is
straightforward.
