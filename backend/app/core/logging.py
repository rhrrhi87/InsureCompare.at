"""Structured logging configuration using structlog.

File: backend/app/core/logging.py
"""
import logging
import sys

import structlog

from app.core.config import settings


def setup_logging() -> None:
    """Configure structlog + stdlib logging at process start.

    Logs are emitted as JSON in production for easy ingestion by log
    aggregators, and as colourised key/value pairs in development.
    """
    # On Windows, sys.stdout defaults to the legacy console code page
    # (cp1252), not UTF-8. This app logs German policy text (ä/ö/ü/ß) as a
    # matter of course, so any log call containing such text — e.g. the
    # exception logger firing while handling an OCR/NLP error — would raise
    # UnicodeEncodeError from *inside* the exception handler and turn a
    # normal 4xx/5xx into an unrelated crash. reconfigure() is a no-op (and
    # harmless) on platforms where stdout is already UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.is_production:
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        shared_processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "watchfiles.main"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger, tagged with ``name`` if given.

    ``structlog.stdlib.add_logger_name`` (the usual way to do this) reads
    ``.name`` off the underlying logger object, which only exists for
    stdlib-backed loggers — this project uses ``PrintLoggerFactory``, whose
    ``PrintLogger`` has no ``.name``, so that processor crashes on every
    call. Binding the name into the event dict directly works with any
    logger_factory.
    """
    logger = structlog.get_logger()
    return logger.bind(logger=name) if name else logger
