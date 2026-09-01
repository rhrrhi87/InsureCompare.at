"""LLM provider factory — selects the provider via LLM_PROVIDER.

File: backend/app/llm/factory.py
"""
from __future__ import annotations

from app.core.config import settings
from app.llm.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider.

    May raise LLMUnavailableError (e.g. GeminiProvider with no API key
    configured) — callers must handle that, not let it propagate raw.
    """
    if settings.LLM_PROVIDER == "mock":
        from app.llm.mock_provider import MockLLMProvider

        return MockLLMProvider()

    from app.llm.gemini_provider import GeminiProvider

    return GeminiProvider()
