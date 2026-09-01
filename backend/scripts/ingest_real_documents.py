"""Ingest real, official Austrian insurer IPID documents through the real
running upload API (not a direct DB insert) so every Upload/Clause row this
produces is genuine, unedited pipeline output.

File: backend/scripts/ingest_real_documents.py

Run with the backend dev server already running on http://localhost:8000::

    python -m scripts.ingest_real_documents
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8000"
DOCS_DIR = Path(__file__).resolve().parents[1] / "data" / "source_documents"
MANIFEST = json.loads((DOCS_DIR / "MANIFEST.json").read_text(encoding="utf-8"))


def login(email: str, password: str) -> str:
    data = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login", data=data, headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp["access_token"]


def upload_pdf(token: str, path: Path) -> dict:
    boundary = "----insurecompare-real-doc-boundary"
    payload = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}/api/documents",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    return json.loads(urllib.request.urlopen(req).read())


def main() -> None:
    missing = [d["filename"] for d in MANIFEST["documents"] if not (DOCS_DIR / d["filename"]).is_file()]
    if missing:
        raise SystemExit(
            "Missing real source PDF(s): "
            + ", ".join(missing)
            + "\nThese are not committed to the repository (see MANIFEST.json's "
            "_redistribution_note). Run `python -m scripts.download_source_documents` first."
        )

    token = login("admin@insurance.at", "admin123")
    results = []
    for doc in MANIFEST["documents"]:
        path = DOCS_DIR / doc["filename"]
        result = upload_pdf(token, path)
        results.append({"manifest": doc, "upload_result": result})
        print(f"Uploaded {doc['filename']} -> upload_id={result.get('id')} status={result.get('status')}")

    out_path = DOCS_DIR / "_ingestion_results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Full results written to {out_path}")


if __name__ == "__main__":
    main()
