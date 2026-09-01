"""LLM provider abstraction for the AI Policy Advisor.

File: backend/app/llm/base.py

InsureCompare.at is the product; Gemini (or the deterministic mock used in
tests) is an interchangeable implementation detail behind this interface.
See docs/AI_ADVISOR_ARCHITECTURE.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMUnavailableError(Exception):
    """Raised whenever the provider cannot produce a usable response.

    Covers: missing/invalid API key, timeout, rate limit, unavailable
    model, malformed/non-schema-conforming output, and network errors.
    Callers must catch this and fall back to a professional "advisor
    unavailable" response (Part 18) — never a raw stack trace.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class LLMProvider(ABC):
    """A provider that turns (system prompt + evidence + question) into a
    validated structured response. Implementations must never fabricate
    evidence IDs beyond what they were given in `user_content`."""

    @abstractmethod
    def generate_structured(
        self, *, system_prompt: str, user_content: str, response_schema: type[T]
    ) -> T:
        """Call the LLM and return a validated instance of `response_schema`.

        Raises LLMUnavailableError on any failure — never lets a raw
        provider exception (network, auth, quota, ...) escape.
        """
        raise NotImplementedError
