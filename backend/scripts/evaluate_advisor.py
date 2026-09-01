"""Reproducible, read-only Advisor evidence-safety evaluation.

This evaluation uses the real PostgreSQL clauses extracted from the official
UNIQA IPID, but forces the deterministic mock LLM.  It therefore measures
retrieval/support decisions, citation validation, document isolation and safe
abstention without an external API call.  It deliberately does not claim to
measure natural-language answer correctness; that requires a separate,
human-rated live-model run.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

os.environ["LLM_PROVIDER"] = "mock"

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.db.models import Clause, Upload  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.services.advisor_service import answer_question  # noqa: E402

FIXTURE_PATH = BACKEND_DIR / "tests" / "fixtures" / "advisor_eval" / "questions.json"
RESULTS_PATH = Path(__file__).resolve().parent / "advisor_evaluation_results.json"


def _term_hit(evidence: list[dict], expected_terms: list[str]) -> bool:
    if not expected_terms:
        return not evidence
    combined = " ".join(str(item["text"]).lower() for item in evidence)
    return any(term.lower() in combined for term in expected_terms)


async def evaluate() -> dict:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    source_filename = fixture["_provenance"]["source_document"]

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Upload)
            .where(Upload.filename == source_filename)
            .order_by(Upload.id.desc())
            .limit(1)
        )
        upload = result.scalar_one_or_none()
        if upload is None:
            return {
                "status": "NOT_VERIFIED",
                "reason": f"No database upload matched {source_filename}.",
                "provider": "mock",
                "source": fixture["_provenance"],
            }

        result = await db.execute(select(Clause).where(Clause.upload_id == upload.id))
        document_clauses = list(result.scalars().all())
        valid_clause_ids = {clause.id for clause in document_clauses}

        cases: list[dict] = []
        for item in fixture["questions"]:
            response = await answer_question(
                db,
                upload=upload,
                question=item["question"],
                language="de",
            )
            actual = response.model_dump()
            evidence = actual["evidence"]
            cited_ids = {int(entry["clause_id"]) for entry in evidence}
            citation_valid = cited_ids.issubset(valid_clause_ids)
            isolation_valid = all(entry["provenance"] == "DOCUMENT_EXTRACTED" for entry in evidence)
            support_correct = bool(actual["supported"]) == bool(item["expected_supported"])
            expected_term_found = _term_hit(evidence, item["expected_evidence_terms"])
            safe_abstention = (
                item["expected_supported"]
                or (
                    not actual["supported"]
                    and not evidence
                    and not actual["key_points"]
                    and not actual["attention_points"]
                )
            )
            cases.append(
                {
                    **item,
                    "actual_response": actual,
                    "checks": {
                        "support_decision_correct": support_correct,
                        "expected_evidence_term_found": expected_term_found,
                        "all_citations_belong_to_selected_document": citation_valid,
                        "all_evidence_has_document_extracted_provenance": isolation_valid,
                        "safe_abstention_for_unsupported_case": safe_abstention,
                    },
                }
            )

    def rate(check_name: str) -> float:
        return round(sum(bool(c["checks"][check_name]) for c in cases) / len(cases), 4)

    supported_cases = [c for c in cases if c["expected_supported"]]
    unsupported_cases = [c for c in cases if not c["expected_supported"]]
    supported_without_evidence = sum(
        bool(c["actual_response"]["supported"]) and not c["actual_response"]["evidence"]
        for c in cases
    )
    return {
        "status": "VERIFIED_WITH_MOCK_PROVIDER",
        "run_timestamp_utc": datetime.now(UTC).isoformat(),
        "provider": "mock",
        "source": fixture["_provenance"],
        "database_selection": {
            "upload_id": upload.id,
            "filename": upload.filename,
            "document_clause_count": len(document_clauses),
        },
        "metrics": {
            "question_count": len(cases),
            "supported_question_count": len(supported_cases),
            "unsupported_question_count": len(unsupported_cases),
            "support_decision_accuracy": rate("support_decision_correct"),
            "expected_evidence_term_hit_rate": rate("expected_evidence_term_found"),
            "citation_validity_rate": rate("all_citations_belong_to_selected_document"),
            "document_isolation_rate": rate("all_evidence_has_document_extracted_provenance"),
            "safe_abstention_rate": round(
                sum(bool(c["checks"]["safe_abstention_for_unsupported_case"]) for c in unsupported_cases)
                / max(len(unsupported_cases), 1),
                4,
            ),
            "supported_answers_without_validated_evidence": supported_without_evidence,
            "semantic_answer_correctness": "NOT_MEASURED",
        },
        "interpretation": (
            "This run verifies the real retrieval and evidence-validation path with a deterministic "
            "provider. The mock response is intentionally generic, so it cannot support a claim "
            "about Gemini answer quality or human-rated semantic correctness."
        ),
        "cases": cases,
    }


async def main() -> None:
    report = await evaluate()
    RESULTS_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": report["status"], "metrics": report.get("metrics")}, indent=2))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
