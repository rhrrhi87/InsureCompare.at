# Data Sources & Provenance Policy

## Principle

InsureCompare.at only uses **publicly available** Austrian insurance
information: Insurance Product Information Documents (IPID), full policy
conditions (AVB), and publicly published product brochures. It never
scrapes or stores non-public customer data, and it never fabricates a
value and presents it as if it came from a real document.

## Current catalogue status: demonstration data

Every catalogue `Policy` row carries an `is_demo_data` flag (default
`true`) plus a set of nullable provenance fields:

| Field | Meaning |
|---|---|
| `document_title` | Title of the source document (e.g. "IPID – Kfz-Haftpflicht") |
| `document_type` | `"IPID"`, `"AVB"`, or similar |
| `source_url` | Public URL the document was retrieved from |
| `source_organisation` | The insurer or public body that published it |
| `retrieval_date` / `last_reviewed_date` | When the entry was sourced/last checked |
| `document_language` | Always `"de"` for Austrian source material |

**As of this build, all seeded catalogue policies (`backend/scripts/seed.py`)
are `is_demo_data=true` with the provenance fields left `null`.** The
premiums, coverage lists and exclusions in the seed catalogue are
illustrative examples for demonstrating the comparison and recommendation
engine — they are **not** transcribed from a specific real insurer document,
and the UI must never present them as if they were (see the "Demonstration
data" badge on `PolicyDetailPage` and the admin policy list).

This is a deliberate, honest scope decision: fabricating plausible-looking
`source_url`/`document_title` values for the seed catalogue would violate
the project's own anti-fabrication rule more seriously than leaving the
fields empty and labelling the data as a demonstration.

## Path to real provenance

The admin catalogue UI (`/admin/policies`) lets an admin uncheck
"Demonstration data" and fill in the four source fields when they have
actually reviewed a real public IPID/AVB document for a policy. Doing so is
a manual, deliberate act — the schema does not auto-populate these fields
from anywhere.

## User-uploaded documents

Documents a user uploads through `/upload` are a completely different,
already-real data path: the file the user provides *is* the source
document. Each `Upload` row and every `Clause` row derived from it
(`extraction_method="ocr_nlp"`) is fully traceable to that specific file,
with page number and OCR/NLP confidence recorded per clause. See
`docs/AI_PIPELINE.md`.

**This path now includes 3 real, official Austrian insurer IPID documents**
(UNIQA Kfz-Haftpflicht "Auto & Frei", Generali Haushaltversicherung,
Wiener Städtische Rechtsschutzversicherung), downloaded directly from each
insurer's own domain and ingested through the real `POST /api/documents`
endpoint. Full source URLs, retrieval dates, and document versions:
`backend/data/source_documents/MANIFEST.json`. These are classified
`VERIFIED_SOURCE` in `docs/DATA_PROVENANCE_AUDIT.md` §4a — the strongest
provenance category this project defines. They were deliberately **not**
turned into `Policy` catalogue rows, because a real IPID does not disclose
an exact premium or sum insured (those are set per-contract), and the
`Policy` schema requires one — inventing a number to fill that field would
itself be the kind of fabrication this policy forbids. See
`docs/DATA_PROVENANCE_AUDIT.md` §7 for the full reasoning.

## Seeded provider catalogue

The seeded provider list (`backend/scripts/seed.py::PROVIDERS`) contains
the real, legally-registered names of 15 genuine Austrian insurers: UNIQA
Österreich Versicherungen AG, Allianz Elementar Versicherungs-AG, WIENER
STÄDTISCHE Versicherung AG – Vienna Insurance Group, Generali Versicherung
AG, DONAU Versicherung AG – Vienna Insurance Group, Zürich
Versicherungs-AG, Grazer Wechselseitige Versicherung AG (GRAWE), Helvetia
Versicherungen AG, ERGO Versicherung AG, VAV Versicherungs-AG, Wüstenrot
Versicherungs-AG, TIROLER VERSICHERUNG V.a.G., Niederösterreichische
Versicherung AG, OBERÖSTERREICHISCHE Versicherung AG, and Europäische
Reiseversicherung AG. These are used here only as **catalogue labels** — no
claim is made that InsureCompare.at has a commercial relationship,
integration, or live pricing feed with any of them. This matches the
project's original scope: no live quotation APIs and no broker-style
contract conclusion.

Each provider's `logo_url` points at an image hosted on that insurer's own
official domain — never a locally-generated, recreated, or third-party-
hosted logo image. No logo file is downloaded or embedded in this
repository; the field is a reference URL, resolved and rendered by the
client at view time, same as before. `rating_score` is a uniform
placeholder (`8.0`) for every provider, since the project has no real,
sourced insurer rating feed — see `docs/DATA_PROVENANCE_AUDIT.md` for the
full per-provider source table (official website, logo URL, source page,
retrieval date, confidence) and the reasoning for the uniform rating.
Nine of the 15 providers currently have no associated `Policy` rows: no
products were invented for them merely to populate the catalogue.

For a full, per-record classification of every provider, policy, premium,
deductible, coverage, exclusion, and extracted clause currently in the
database — `VERIFIED_SOURCE` / `DOCUMENT_EXTRACTED` / `DERIVED` /
`DEMO_SYNTHETIC` / `UNKNOWN` — see `docs/DATA_PROVENANCE_AUDIT.md`.
