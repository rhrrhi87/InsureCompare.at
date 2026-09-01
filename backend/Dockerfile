# File: backend/Dockerfile
# Multi-stage build for the InsureCompare.at FastAPI backend.
#
# Stage 1 ("builder") installs build deps and compiles wheels.
# Stage 2 ("runtime") installs only runtime libs and copies the wheels.

# =============================================================================
# Stage 1 - builder
# =============================================================================
FROM python:3.11-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt ./
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# =============================================================================
# Stage 2 - runtime
# =============================================================================
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Install runtime libraries:
#  - libpq5 for asyncpg
#  - tesseract + German language pack for OCR
#  - poppler-utils provides pdftoppm (used by some OCR fallbacks)
#  - curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr \
    tesseract-ocr-deu \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --system app && useradd --system --gid app --create-home --home-dir /home/app app

WORKDIR /app

# Install pre-built wheels from the builder stage
COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

# Optional: pre-fetch the German spaCy model. Keeps cold-start under control.
# Comment out if you want a slimmer image or lazy-load at first request.
RUN python -m spacy download de_core_news_lg || true

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini pyproject.toml ./
COPY scripts ./scripts

# Drop to non-root
RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://localhost:${PORT}/api/healthz || exit 1

# Apply DB migrations on startup, then run uvicorn.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2"]
