"""Deterministic mock LLM provider — used for pytest/E2E/CI.

File: backend/app/llm/mock_provider.py

Automated tests must not call the real Gemini API repeatedly (Part 19).
This provider never makes a network call; it derives a plausible,
deterministic structured response purely from the evidence IDs present in
`user_content`, so tests can exercise both the "supported" and
"unsupported / cannot confirm" paths without any live API dependency.
Set LLM_PROVIDER=mock (the default) to use it.
"""
from __future__ import annotations

import json
import re

from app.llm.base import LLMProvider, T
from app.schemas.advisor import AdvisorResponse, AdvisorSummary

_EVIDENCE_ID_RE = re.compile(r'"evidence_id":\s*(\d+)')


def _extract_evidence_ids(user_content: str) -> list[int]:
    return [int(m) for m in _EVIDENCE_ID_RE.findall(user_content)]


def _extract_clause_types(user_content: str) -> list[str]:
    match = re.search(r"VERFÜGBARE BELEGE.*?(\[.*\])", user_content, re.DOTALL)
    if not match:
        return []
    try:
        items = json.loads(match.group(1))
    except (json.JSONDecodeError, TypeError):
        return []
    return [item.get("clause_type", "") for item in items if isinstance(item, dict)]


class MockLLMProvider(LLMProvider):
    def generate_structured(
        self, *, system_prompt: str, user_content: str, response_schema: type[T]
    ) -> T:
        evidence_ids = _extract_evidence_ids(user_content)
        clause_types = _extract_clause_types(user_content)
        is_german = "Du bist" in system_prompt or "Beleg" in user_content

        if response_schema is AdvisorResponse:
            if not evidence_ids:
                answer = (
                    "Diese Information konnte aus dem hochgeladenen Dokument nicht "
                    "eindeutig bestätigt werden."
                    if is_german
                    else "This information could not be confirmed from the uploaded document."
                )
                return AdvisorResponse(  # type: ignore[return-value]
                    answer=answer, supported=False, evidence_ids=[], key_points=[], attention_points=[]
                )
            answer = (
                f"Basierend auf den verfügbaren Belegen (Beleg {evidence_ids[0]}) lässt sich "
                "dies wie folgt beantworten."
                if is_german
                else f"Based on the available evidence (evidence {evidence_ids[0]}), this can be answered as follows."
            )
            return AdvisorResponse(  # type: ignore[return-value]
                answer=answer,
                supported=True,
                evidence_ids=evidence_ids,
                key_points=["Mock key point"] if is_german else ["Mock key point"],
                attention_points=[],
            )

        if response_schema is AdvisorSummary:
            if not evidence_ids:
                return AdvisorSummary(evidence_ids=[])  # type: ignore[return-value]
            return AdvisorSummary(  # type: ignore[return-value]
                insurance_type=clause_types[0] if clause_types else None,
                main_coverages=["Mock coverage"],
                important_exclusions=["Mock exclusion"] if "exclusion" in clause_types else [],
                strengths=["Mock strength"],
                attention_points=["Mock attention point"],
                evidence_ids=evidence_ids,
            )

        raise ValueError(f"MockLLMProvider has no fixture for schema {response_schema}")
