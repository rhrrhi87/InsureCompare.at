# Database

PostgreSQL 16, SQLAlchemy 2.0 async ORM, Alembic migrations
(`backend/alembic/versions/`). pgvector is available for the `Clause.embedding`
column but the column is currently plain JSON — see the migration note in
`app/db/models/policy.py`; switching to a native `vector` column is a
drop-in change that doesn't touch application code.

## Entities

| Table | Purpose |
|---|---|
| `users` | Accounts, bcrypt password hash, role (`user`/`admin`) |
| `sessions` | Refresh-token rotation/revocation (hash only, never the token) — see `docs/SECURITY.md` |
| `risk_profiles` | One per user: preferences + optional custom scoring weights |
| `providers` | Insurer catalogue (name, country, rating, active flag) |
| `policies` | Product catalogue: pricing, coverage/exclusion lists, risk level, provenance fields, `is_active`/`retired_at` |
| `clauses` | Source-evidence rows — linked to *either* a `policy_id` (catalogue) *or* an `upload_id` (personal document), never both |
| `uploads` | User-submitted documents + OCR/NLP pipeline results (status, confidence, extracted JSON) |
| `recommendations` | Persisted ranked results + the exact weights used (audit/reproducibility) |
| `audit_logs` | Append-only high-value action log |

## Design decisions worth flagging to a viva examiner

- **`policies.is_active` + `retired_at`, never a hard delete.** The
  `PolicyService.retire_policy`/`reactivate_policy` methods are the only
  way to change a policy's active state via the API — there is no DELETE
  endpoint. This exists specifically so a `Recommendation.ranked_policies`
  snapshot from six months ago stays reproducible even if the underlying
  policy is later retired. Providers follow the same rule
  (`set_provider_active`, never hard-deleted, since cascading a provider
  delete would also destroy its policies).
- **`clauses.policy_id` is nullable**, `clauses.upload_id` is nullable —
  exactly one is set per row. This lets one table serve both catalogue
  evidence (admin-entered/sourced) and personal-upload evidence (pipeline
  -extracted) without two near-duplicate tables.
- **`policies.is_demo_data`** defaults `true`. See `docs/DATA_SOURCES.md`
  for why the seed catalogue is honestly labelled rather than given
  fabricated source citations.
- **Denormalised JSON + canonical rows, applied consistently.**
  `Policy.coverage_items`/`exclusions` (fast-read JSON lists of concept
  strings) coexist with `Clause` rows (canonical, page-level evidence) for
  policies; the same pattern is used for `Upload.extracted` (fast-read JSON
  summary) alongside `Clause` rows for uploads. One pattern, two places it
  applies — not two different designs.
- **Naming convention** (`app/db/base.py::NAMING_CONVENTION`) gives every
  index/constraint a deterministic name, so Alembic autogenerate diffs stay
  readable across the project's lifetime.

## Migrations

- `0001_initial` — the original 8-table schema.
- `0002_provenance_sessions_clause_types` — adds `sessions`; adds the
  provenance + retirement columns to `policies`; adds `upload_id` /
  `document_language` / `extraction_method` to `clauses` and makes
  `clauses.policy_id` nullable; extends the `clause_type` Postgres enum
  with `deductible`/`obligation`/`territorial_scope`/`duration`/
  `optional_benefit`. PostgreSQL cannot remove enum values, so the
  `clause_type` extension is one-way — documented in the migration's
  `downgrade()`.

Tests run against SQLite in-memory and build the schema directly from the
SQLAlchemy models (`Base.metadata.create_all`), not through Alembic — this
is a deliberate speed/simplicity trade-off already established in the
codebase (`backend/tests/conftest.py`) and is why the enum-extension
migration's Postgres-specific `ALTER TYPE ... ADD VALUE` mechanics don't
need a SQLite equivalent.
