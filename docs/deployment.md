# Deployment

## Local quickstart (Docker)

Prerequisites: Docker 24+, Docker Compose v2, OpenSSL.

```bash
git clone https://github.com/<you>/insurecompare.git
cd insurecompare

# Generate dev TLS cert + .env
cp .env.example .env
./nginx/generate-dev-certs.sh

# Build and start
docker compose up --build -d

# Tail logs (optional)
docker compose logs -f api
```

The stack is reachable at:

| URL                              | Service                            |
|----------------------------------|------------------------------------|
| https://localhost                | Frontend SPA                       |
| https://localhost/api/healthz    | Backend liveness probe             |
| https://localhost/docs           | OpenAPI / Swagger                  |
| postgres://app@localhost:5432    | Postgres (only if dev override on) |

Demo accounts seeded automatically:

- `user@test.at` / `user123`
- `admin@insurance.at` / `admin123`

## Local development (no Docker for the frontend)

```bash
# 1. Backend with the docker DB
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db api

# 2. Frontend on the host
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api to the backend
```

## Database migrations

Migrations are managed by Alembic and run automatically on container start
(`alembic upgrade head` is part of the API container CMD).

Manual operations:

```bash
docker compose exec api alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "describe change"
docker compose exec api alembic downgrade -1
```

## Seeding

The compose file ships a one-shot `seed` service that runs after the API is
ready. Re-run manually with:

```bash
docker compose run --rm seed
```

The script is idempotent: existing providers, policies and demo users are
left in place.

## Production checklist

- Replace dev TLS certs in `nginx/certs/` with real ones (Let's Encrypt
  recommended; ACME challenge path is already routed).
- Set `JWT_SECRET` to a 32-byte random hex string (`openssl rand -hex 32`).
- Set `ENVIRONMENT=production` and `LOG_LEVEL=INFO`.
- Restrict `BACKEND_CORS_ORIGINS` to the public domain only.
- Replace the in-process rate limiter with Redis if running multiple API
  replicas (the interface is already a Starlette middleware; swap in
  `slowapi` backed by `aioredis`).
- Switch JWT to RS256 with a managed key pair (already supported by
  `app.core.security`; only the `JWT_ALGORITHM` setting + key files need to
  change).
- Move uploaded documents from in-DB JSON to S3-compatible object storage and
  swap `UploadService.ingest` to write the binary there. Storage key already
  follows the `uploads/{user_id}/{sha256}` convention.
- Configure container log drivers for JSON output (default in production
  thanks to `setup_logging`).
- Add a Postgres backup strategy (e.g. `pg_dump` to S3 nightly).

## Scaling

The API is fully stateless and can be scaled horizontally:

```bash
docker compose up -d --scale api=3
```

The compose `proxy` already round-robins via the `api_upstream` block. For
larger deployments, replace docker compose with Kubernetes (the Dockerfiles
require no changes; helm chart not included in this repository).
