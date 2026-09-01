# Local development without Docker

## Prerequisites

- Python 3.11+
- Node 20+
- PostgreSQL 16 running locally (or via the docker DB service)
- Tesseract 5 with the German language pack:
  - macOS: `brew install tesseract tesseract-lang`
  - Debian/Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-deu`

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python -m spacy download de_core_news_lg

cp ../.env.example ../.env       # edit JWT_SECRET, DATABASE_URL etc.
export $(grep -v '^#' ../.env | xargs)

# Apply migrations + seed
alembic upgrade head
python -m scripts.seed

# Run
uvicorn app.main:app --reload --port 8000
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs on http://localhost:5173 and proxies `/api` to
http://localhost:8000 (configured in `vite.config.ts`).

## Tests

```bash
# Backend
cd backend && pytest -q

# Frontend
cd frontend && npm test
```

## Useful one-liners

```bash
# Open the OpenAPI explorer
open http://localhost:8000/docs

# Tail the backend logs while debugging
ENVIRONMENT=development LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Check the DB schema
docker compose exec db psql -U app -d insurecompare -c '\dt'
```
