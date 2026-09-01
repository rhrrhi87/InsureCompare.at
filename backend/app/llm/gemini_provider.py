"""Google Gemini implementation of the LLM provider interface.

File: backend/app/llm/gemini_provider.py

Uses the official `google-genai` SDK (https://googleapis.github.io/python-genai/).
Model is configurable via GEMINI_MODEL (default: gemini-3.6-flash, the
Flash model currently available to new Gemini API users and suitable for
structured JSON output in German and English).

The API key is read server-side only from GEMINI_API_KEY (see
app/core/config.py) and is never exposed to the frontend or logged.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger
from app.llm.base import LLMProvider, LLMUnavailableError, T

logger = get_logger("llm.gemini")


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise LLMUnavailableError("missing_api_key")

        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - dependency always installed in practice
            raise LLMUnavailableError("sdk_not_installed") from exc

        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_structured(
        self, *, system_prompt: str, user_content: str, response_schema: type[T]
    ) -> T:
        from google.genai import errors, types

        try:
            response = self._client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                    temperature=0.1,
                ),
            )
        except errors.APIError as exc:
            # Covers invalid/expired key (401/403), rate limit (429),
            # unavailable model (404), and most server-side failures.
            logger.warning("gemini api error", code=getattr(exc, "code", None), error=str(exc))
            raise LLMUnavailableError("api_error") from exc
        except Exception as exc:  # timeout, DNS/network failure, etc.
            logger.warning("gemini call failed", error=str(exc))
            raise LLMUnavailableError("network_error") from exc

        text = getattr(response, "text", None)
        if not text:
            logger.warning("gemini returned empty response")
            raise LLMUnavailableError("empty_response")

        try:
            return response_schema.model_validate_json(text)
        except Exception as exc:
            logger.warning("gemini output failed schema validation", error=str(exc))
            raise LLMUnavailableError("malformed_output") from exc
