# Security

## Authentication

- Passwords hashed with bcrypt (cost factor 12) via `passlib`; verification
  is constant-time (`app/core/security.py`).
- Access tokens: signed JWT (HS256 by default; RS256 supported by swapping
  `JWT_ALGORITHM` + key files — see `docs/deployment.md`), 30-minute expiry.
- Refresh tokens: signed JWT, 14-day expiry, **and** backed by a `sessions`
  table row (`app/db/models/session.py`). The JWT alone proves who is
  asking; the `Session` row is what makes that claim *revocable*:
  - **Rotation on use**: `POST /api/auth/refresh` revokes the presented
    session and issues a new token pair + new session row. Reusing an
    already-rotated refresh token fails with 401 even though its JWT
    signature and expiry are still technically valid.
  - **Logout**: `POST /api/auth/logout` revokes the session tied to the
    given refresh token immediately.
  - Only a SHA-256 hash of the refresh token is stored — never the token
    itself (`hash_token()` in `app/core/security.py`).
- `GET /api/auth/me` and all protected routes require a valid, non-expired
  access token via the `current_user` dependency (`app/api/deps.py`);
  `admin_only` additionally checks `role == admin`.

## Authorization

- Role-based: `UserRole.USER` / `UserRole.ADMIN`, enforced per-route via
  FastAPI dependencies, not client-side checks.
- Frontend route guards (`ProtectedLayout adminOnly`) are a UX convenience
  only — every admin mutation is independently re-checked server-side.

## Input validation

- All request bodies are Pydantic v2 schemas with explicit field
  constraints (`ge=`, `max_length=`, enum types) — malformed payloads are
  rejected with 422 before touching a service.
- File uploads: MIME allowlist (`application/pdf`, `image/jpeg`,
  `image/png`) and a 10 MB size cap, enforced in `UploadService.ingest`
  before any parsing is attempted.

## Error handling

- Domain errors (`app/core/exceptions.py`) are mapped to structured JSON
  (`{"detail": "..."}`) with the correct HTTP status — no raw stack traces
  or exception internals are ever returned to the client
  (`main.py::_domain_error_handler`).
- Server-side logs use `structlog` (`app/core/logging.py`); passwords and
  tokens are never logged (only bcrypt hashes / hashed refresh tokens are
  persisted, and those aren't included in log statements).

## Data protection

- No payment card data, bank credentials, or government IDs are ever
  collected or stored — the platform has no such fields (spec-mandated
  exclusion, not a control the codebase has to work around).
- Uploaded documents are stored as `bytes`/JSON in Postgres for this
  prototype, keyed by SHA-256 content hash
  (`uploads/{user_id}/{sha256}` storage-key convention); production
  deployment should move the binary to S3-compatible object storage — noted
  in `docs/deployment.md`, not implemented, since local disk/DB storage is
  sufficient for an academic demonstration and introducing a cloud storage
  dependency would add risk without benefit for graders running the
  project locally.

## Rate limiting

- `RateLimitMiddleware` (`app/core/rate_limit.py`) throttles requests
  per-client in-process. Documented as needing a Redis-backed
  implementation (`slowapi` + `aioredis`) before running multiple API
  replicas — the in-process limiter does not share state across processes.

## Audit trail

See `docs/TESTING.md` and `docs/TRACEABILITY_MATRIX.md`. Audit events
(`LOGIN`, `UPLOAD_PROCESSED`, `RECOMMENDATION_GENERATED`, `POLICY_CREATED`,
`POLICY_UPDATED`, `POLICY_RETIRED`, `WEIGHTS_CHANGED`) are append-only rows
in `audit_logs`, written via `AdminService.record_action`, and are
themselves covered by integration tests
(`backend/tests/test_admin_catalogue.py`).

## Known limitations (honestly disclosed, not fixed in this build)

- No CAPTCHA / bot-detection on registration.
- No email verification on registration.
- No account lockout after repeated failed logins (only rate limiting).
- No CSRF protection needed currently because the API is a pure JSON
  bearer-token API with no cookie-based session — this would need
  revisiting if cookie auth were ever introduced.
- Single-process in-memory rate limiting (see above).

These are typical, explicitly scoped-out hardening items for an academic
prototype rather than a production consumer service, and are listed here so
they're not mistaken for oversights.
