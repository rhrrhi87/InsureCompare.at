"""FastAPI application entrypoint.

File: backend/app/main.py

Run with::

    uvicorn app.main:app --host 0.0.0.0 --port 8000

The factory wires together the API routers, middleware (CORS + rate limiting),
exception handlers, and OpenAPI metadata.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse

from app.api import (
    admin,
    advisor,
    auth,
    compare,
    documents,
    health,
    policies,
    profiles,
    recommendations,
)
from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.logging import get_logger, setup_logging
from app.core.rate_limit import RateLimitMiddleware

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan hook (startup + shutdown)."""
    setup_logging()
    logger.info(
        "InsureCompare backend starting",
        environment=settings.ENVIRONMENT,
        cors=settings.cors_origins,
    )
    yield
    logger.info("InsureCompare backend shutting down")


def create_app() -> FastAPI:
    """Construct the FastAPI app."""
    app = FastAPI(
        title="InsureCompare.at API",
        description=(
            "AI-powered Austrian insurance comparison platform. "
            "Built for the SWE6010 BEng Software Engineering dissertation."
        ),
        version="1.0.0",
        default_response_class=ORJSONResponse,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ---- Middleware ----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE
    )

    # ---- Routers ----
    api_routers = [
        health.router,
        auth.router,
        profiles.router,
        policies.router,
        documents.router,
        advisor.router,
        recommendations.router,
        compare.router,
        admin.router,
    ]
    for router in api_routers:
        app.include_router(router, prefix="/api")

    # ---- Exception handlers ----
    @app.exception_handler(DomainError)
    async def _domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        logger.warning("Domain error", status=exc.status_code, detail=exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/", include_in_schema=False)
    async def _root() -> dict[str, str]:
        return {
            "service": "InsureCompare.at API",
            "version": app.version,
            "docs": "/docs",
        }

    return app


app = create_app()
