"""Reproducibly re-download the real official insurer documents.

File: backend/scripts/download_source_documents.py

The 3 real IPID PDFs used for the academic evaluation (see
docs/DATA_PROVENANCE_AUDIT.md §4a) are NOT committed to this repository —
redistribution permission for third-party insurer PDFs is unclear, even
though the documents are freely publicly available. This script restores
them from their official source URLs, recorded in
backend/data/source_documents/MANIFEST.json, and verifies each download's
sha256 checksum against the one recorded when the documents were first
retrieved (2026-08-28), so a fresh clone can reproduce exactly the same
evaluation inputs.

Run with::

    python -m scripts.download_source_documents

Then, to reproduce the real-document ingestion and evaluation:

    python -m scripts.ingest_real_documents   # requires the backend dev server running
    python -m scripts.evaluate_nlp
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[1] / "data" / "source_documents"
MANIFEST_PATH = DOCS_DIR / "MANIFEST.json"


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    for doc in manifest["documents"]:
        dest = DOCS_DIR / doc["filename"]
        print(f"Downloading {doc['filename']} from {doc['source_url']} ...")
        req = urllib.request.Request(doc["source_url"], headers={"User-Agent": "Mozilla/5.0"})
        payload = urllib.request.urlopen(req, timeout=30).read()

        actual_sha256 = hashlib.sha256(payload).hexdigest()
        expected_sha256 = doc["sha256"]
        if actual_sha256 != expected_sha256:
            print(
                f"  WARNING: checksum mismatch for {doc['filename']}.\n"
                f"    expected: {expected_sha256}\n"
                f"    actual:   {actual_sha256}\n"
                "  The insurer may have updated the document since it was first "
                "retrieved (IPIDs are periodically revised) — re-run the real-document "
                "evaluation and update docs/NLP_EVALUATION.md / MANIFEST.json if so. "
                "Do not silently trust a mismatched file."
            )
        else:
            print(f"  OK — sha256 matches ({actual_sha256[:16]}...)")

        dest.write_bytes(payload)

    print(f"\nAll documents downloaded to {DOCS_DIR}")


if __name__ == "__main__":
    main()
