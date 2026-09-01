# Data Provenance Audit

File: `docs/DATA_PROVENANCE_AUDIT.md`
Audit date: 2026-08-28 (updated same day, twice: real-document ingestion
phase, then the final repository freeze / academic consistency review)
Auditor: Claude (this session), acting as lead engineer on this codebase

**Update note (real-document phase)**: this document originally stated
"no record in this project is currently `VERIFIED_SOURCE`". That is no
longer true — §4a below documents 3 real, officially-published Austrian
insurer documents that were downloaded and ingested through the real
pipeline in this same session.

**Update note (final freeze)**: as part of the pre-commit repository
freeze, the synthetic-fixture uploads originally described in §4b were
**removed from the development database** (13 rows: 3 uploads of a
manually-generated, never-committed test image, plus 10 duplicate uploads
of `frontend/e2e/fixtures/test_policy.png` accumulated from repeated E2E
test runs). §4b is kept below, clearly marked as historical, because the
findings it documents (e.g. the 94%/19–41%-confidence pattern) are already
independently corroborated by §4a's real-document results and by
`docs/NLP_EVALUATION.md`'s reproducible synthetic-fixture evaluation — no
evidence needed to reproduce a documented result was lost. See §8 for the
full cleanup rationale and the resulting database state.

**Research claim boundary** (see also README.md and
`docs/NLP_EVALUATION.md`): the real documents in §4a validate document
ingestion, PDF text extraction, OCR, clause extraction, and clause
classification against genuine Austrian insurance sources. They do **not**
mean the comparison/recommendation catalogue is priced from real insurer
quotations — the 12 `Policy` rows in §2 remain `DEMO_SYNTHETIC`, precisely
because real IPIDs (§7) do not disclose the premium/coverage-limit figures
that catalogue needs. Do not read §4a as validating the catalogue's
pricing; it validates the document-understanding pipeline only.

## Purpose and method

This document classifies **every record currently in the running database**
(verified by direct query against the local PostgreSQL 16 instance on
2026-08-28, not by reading source code alone) into one of five categories:

| Classification | Meaning |
|---|---|
| `VERIFIED_SOURCE` | Traceable to a specific, real, publicly-published document (URL + document identity recorded) |
| `DOCUMENT_EXTRACTED` | Produced by the real OCR/NLP pipeline from an actual uploaded file, but that file is a synthetic/test fixture, not a real insurer document |
| `DERIVED` | Computed from other in-database values (no independent provenance of its own) |
| `DEMO_SYNTHETIC` | Hand-authored for demonstration purposes; realistic but not transcribed from any real document |
| `UNKNOWN` | Origin cannot currently be established from the data or the codebase history |

As of this update, **3 real, official Austrian insurer documents have been
ingested and are `VERIFIED_SOURCE`** — see §4a. This was not true earlier
in the project (see the superseded discussion retained in "Why no
`VERIFIED_SOURCE` records existed before this update" below, kept for the
audit trail).

## 1. Providers (15 rows)

**Classification: `DEMO_SYNTHETIC` for `rating_score`; a distinct, better
category for `name`/`logo_url`, described below.**

All 15 provider names (`backend/scripts/seed.py::PROVIDERS`) are the real,
legally-registered names of genuine Austrian insurance companies — this part
is **factual, not synthetic**. Each `logo_url` points at that insurer's own
public website, researched and verified live (HTTP 200 / correct render) on
2026-08-28. Full source table:

| Provider | Official website | Logo URL (own domain) | Source page | Confidence |
|---|---|---|---|---|
| UNIQA Österreich Versicherungen AG | uniqa.at | a.storyblok.com/f/172351/184x33/c5c80da7aa/uniqa-logo.svg | Header, uniqa.at/versicherung/startseite.html | High |
| Allianz Elementar Versicherungs-AG | allianz.at | allianz.at/content/dam/onemarketing/system/allianz-logo.svg | Header, allianz.at | High |
| WIENER STÄDTISCHE Versicherung AG – VIG | wienerstaedtische.at | wienerstaedtische.at/_assets/.../wstv_logo.svg | Header, wienerstaedtische.at | High |
| Generali Versicherung AG | generali.at | generali.at/static/lg_generali_horizonal_red-....svg | Header, generali.at | High |
| DONAU Versicherung AG – VIG | donauversicherung.at | donauversicherung.at/_assets/.../donau-logo.svg | Header, donauversicherung.at | High |
| Zürich Versicherungs-AG | zurich.at | zurich.at/-/media-assets/.../zurich-logo-blue.svg | Header, zurich.at | High — public brand drops the umlaut ("Zurich") |
| Grazer Wechselseitige Versicherung AG (GRAWE) | grawe.at | grawe.at/_assets/.../grawe-logo.svg | Header, grawe.at | High — site blocks naive `curl`, asset confirmed via live browser render |
| Helvetia Versicherungen AG | helvetia.com/at | helvetia.com/content/dam/os/at/.../helvetia-logo-color-pos-170px.svg | helvetia.com/at/web/de/privatkunden.html | High |
| ERGO Versicherung AG | ergo-versicherung.at | ergo-versicherung.at/_assets/.../ergo-logo-claim.svg | Header, ergo-versicherung.at | High |
| VAV Versicherungs-AG | vav.at | vav.at/dam/jcr:.../VAV-LOGO_CMYK.png | Header, vav.at/privat | High |
| Wüstenrot Versicherungs-AG | wuestenrot.at | wuestenrot.at/content/dam/wuestenrot-aem/home/LogoDesktop.svg | wuestenrot.at/de/home.html | High |
| TIROLER VERSICHERUNG V.a.G. | tiroler-versicherung.at | tiroler-versicherung.at/extension/.../tiroler_neu.svg | Header, tiroler-versicherung.at | High |
| Niederösterreichische Versicherung AG | nv.at | nv.at/nv/logos/nv-logos/nv_logo_2022_hoch_rgb.png | Header, nv.at | High — public brand is "NV" |
| OBERÖSTERREICHISCHE Versicherung AG | versich.at | versich.at/build/images/logo/logo-double-line.svg | Header, versich.at | High — public domain/brand is "versich.at" / "OÖ Versicherung" |
| Europäische Reiseversicherung AG | europaeische.at | europaeische.at/typo3conf/.../erv_logo_L.png | Header, europaeische.at | High |

Retrieval method: each URL was located in that insurer's own page header
markup (`<img>`/`<source>` `src`/`alt` attributes) via a live browser
session, then re-requested directly to confirm it resolves — **not**
downloaded, re-encoded, or embedded as a binary asset in this repository.
`Provider.logo_url` is a reference URL only, per the project's existing
"no logo files stored in-repo" design (see `docs/DATA_SOURCES.md`). Two
sites (allianz.at's CDN, grawe.at) return `403` to a scripted `curl`
request but rendered the exact asset correctly in an interactive browser
session — noted here so a future automated link-checker does not mistake
that for a broken source.

`rating_score` is set to a **uniform placeholder (8.0)** for all 15 rows.
This is intentionally `DEMO_SYNTHETIC` and explicitly **not** presented as a
real market rating: the project has no licensed or sourced rating feed
(e.g. no AKI/VVO index, no Standard & Poor's insurer financial strength
rating), so assigning different-looking numbers per insurer — as the
codebase did before this audit (8.0–8.8, invented per-provider) — would
have implied a differentiated, sourced rating that does not exist. That
prior differentiation has been corrected as part of this audit (see
`backend/scripts/seed.py`).

**Action taken:** none of the 15 providers required new fabrication; the
prior 6-provider catalogue's differentiated `rating_score` values were
corrected to a uniform, clearly-placeholder value.

## 2. Policies / products (12 rows)

**Classification: `DEMO_SYNTHETIC` (all 12 rows, unchanged by this audit).**

Every `Policy` row already carries `is_demo_data=true` (verified by direct
query: 12/12 rows). Premiums, deductibles, coverage limits, coverage items,
additional features and exclusions are illustrative example data written to
exercise the comparison and recommendation engine — they are not
transcribed from any specific real insurer product sheet. This was already
documented in `docs/DATA_SOURCES.md` prior to this audit and remains
accurate; this audit re-verified it against the live database rather than
assuming the documentation was still current.

Per Phase 1's explicit instruction, **no new policies were invented** for
the 9 newly-added providers. 9 of the 15 providers therefore currently have
zero associated policies in the catalogue — this is visible in the admin
provider list and is the honest state, not a bug to be silently patched
over with invented products.

Provenance fields already present on the `Policy` model
(`document_title`, `document_type`, `source_url`, `source_organisation`,
`retrieval_date`, `last_reviewed_date`) are `NULL` for all 12 rows,
consistent with `is_demo_data=true`.

## 3. Coverage / exclusion / limit / deductible values on Policies

**Classification: `DEMO_SYNTHETIC`**, same basis as §2 — these are fields
on the same 12 demo `Policy` rows, not independently-sourced records.

## 4a. Real official documents (4 uploads) and their extracted clauses (148 rows)

**Classification: `VERIFIED_SOURCE`** (the documents themselves) **+
`DOCUMENT_EXTRACTED`** (the clauses the real pipeline produced from them).
This is the strongest provenance combination the taxonomy defines: a real,
currently-published, own-domain document, run through the unedited
production pipeline.

| Upload ID | Filename | Insurer | Product | Official source URL | Retrieval date | Pipeline result |
|---|---|---|---|---|---|---|
| 15 | `uniqa_kfz_haftpflicht_ipid.pdf` | UNIQA Österreich Versicherungen AG | Auto & Frei (Kfz-Haftpflicht) | uniqa.at/versicherung/f/172351/x/297ae8c004/uat_ipid_kfz-haftpflicht.pdf | 2026-08-28 | Vector-PDF text extraction (no OCR needed — genuine digital PDF), 46 clauses |
| 16 | `generali_haushalt_ipid.pdf` | Generali Versicherung AG | Haushaltversicherung | eu-assets.contentstack.com/.../IPID_SachHaushalt_244001.pdf (linked live from generali.at) | 2026-08-28 | Vector-PDF text extraction, 47 clauses |
| 17 | `wienerstaedtische_rechtsschutz_ipid.pdf` | WIENER STÄDTISCHE Versicherung AG – VIG | Rechtsschutzversicherung | wienerstaedtische.at/fileadmin/user_upload/Dokumente/IPID/IPID_NKS_Rechtsschutzversicherung.pdf | 2026-08-28 | Vector-PDF text extraction, 35 clauses |
| 18 | `uniqa_kfz_haftpflicht_page1_real_scan.png` | UNIQA Österreich Versicherungen AG | Auto & Frei (Kfz-Haftpflicht), page 1 | Same source as upload 15 — this is a 200 DPI rasterisation of that real PDF's page 1, uploaded as an image to genuinely force the OCR code path (see §6) | 2026-08-28 | Genuine Tesseract OCR (`used_ocr=true`), 92.6% mean confidence, 20 clauses |

Full source metadata (document type=IPID, document version/date, source
page, retrieval method, sha256 checksum) for each: the tracked
`backend/data/source_documents/MANIFEST.json`. The PDFs/PNG themselves and
the raw ingestion API responses are **not committed** to the repository —
see §8 for why and how to reproduce them. Ingested via
`backend/scripts/ingest_real_documents.py`, which calls the real
`POST /api/documents` endpoint (not a direct DB insert) so every
`Upload`/`Clause` row is genuine, unedited pipeline output — identical code
path to a real user's upload.

**Uploads 15–17 are genuine digital (vector) PDFs**, so the pipeline
correctly took the pdfminer text-extraction path and never invoked OCR for
them. **Upload 18 exists specifically to genuinely exercise the OCR code
path against real content** (§6), since none of the 3 real source PDFs
would trigger it on their own.

Real, automatically-extracted-and-classified `Clause` rows' confidence
statistics (from the live zero-shot classifier, verified by direct query):

| Document | Clauses | Mean confidence | Min | Max |
|---|---|---|---|---|
| UNIQA Kfz-Haftpflicht | 46 | 0.333 | 0.160 | 0.749 |
| Generali Haushaltversicherung | 47 | 0.279 | 0.178 | 0.542 |
| Wiener Städtische Rechtsschutz | 35 | 0.336 | 0.178 | 0.580 |

This independently confirms, on real documents, the same weak-confidence
pattern already found on synthetic fixtures and reported in
`docs/NLP_EVALUATION.md` — not a coincidence of the synthetic test data.

### DERIVED comparison concept: real per-document clause-type distribution

The table below is **`DERIVED`**: computed by counting the hand-labelled
ground-truth entries in
`backend/tests/fixtures/nlp_eval/real_clause_classification_dataset.json`
per `source_document`. It is fully traceable — every count is a sum over
rows that each cite their exact source document and carry the real
sentence text; nothing here is itself a source, it is a derived summary
*of* the 3 `VERIFIED_SOURCE` documents above.

| Clause type | UNIQA (Kfz) | Generali (Haushalt) | Wiener Städtische (Rechtsschutz) |
|---|---|---|---|
| coverage | 3 | 4 | 3 |
| exclusion | 9 | 4 | 4 |
| limit | 1 | 1 | 2 |
| deductible | 0 | 0 | 1 |
| obligation | 6 | 3 | 3 |
| definition | 0 | 0 | 0 |
| territorial_scope | 2 | 2 | 2 |
| duration | 2 | 1 | 2 |
| optional_benefit | 2 | 0 | 0 |
| other | 1 | 1 | 0 |
| **Total real labelled clauses** | **26** | **16** | **17** |

Observation (derived, not itself a new source claim): all 3 real documents
have zero `definition` clauses — IPIDs are a legally standardized terse
summary format and do not contain the kind of defined-terms section found
in full policy wording (AVB), which this project has not sourced. The
UNIQA motor document has proportionally the most exclusions (9 of 26,
~35%), consistent with motor liability cover carrying more statutory
exclusion conditions (alcohol, no licence, unauthorised drivers) than a
household or legal-protection IPID.

## 4b. Synthetic-fixture uploads — HISTORICAL, removed from the database on 2026-08-28

**These rows no longer exist.** As part of the final pre-commit repository
freeze (§8), 13 QA/test-debris upload rows were deleted: the 3 rows
described below (`test_german_policy.png`, a manually-generated image that
was never saved as a committed fixture and so could not be reproduced
anyway) plus 10 duplicate uploads of `frontend/e2e/fixtures/test_policy.png`
that had accumulated from repeatedly running the Playwright E2E suite
during development. This section is kept, clearly marked historical, for
audit-trail completeness — the findings below remain true of what was
observed at the time, they just no longer correspond to live database rows.

**Classification (at the time): `DOCUMENT_EXTRACTED`** — genuinely produced by the real
OCR (Tesseract) + NLP extraction pipeline (`app/nlp/ocr.py`,
`app/nlp/extractor.py`) running against an actually-uploaded file. This is
categorically different from `DEMO_SYNTHETIC`: nothing about the clause
text or confidence score was hand-typed into the database — it is the
pipeline's real, unedited output.

However, honesty requires flagging the input itself: all 3 uploads on
record (`test_german_policy.png`) are a **synthetically-generated test
image** created during this project's own verification work (PIL-rendered
German policy text with known ground truth), not a real insurer's IPID or
AVB scan. So:

- The **extraction process** (OCR → sentence split → classification →
  regex/vocabulary extraction) is real and unedited — `DOCUMENT_EXTRACTED`
  is the correct label for *how the record was produced*.
- The **underlying document** is a controlled test fixture, not a real
  insurer publication — so these clauses must **not** be presented in any
  report or UI surface as evidence about a real insurer's actual policy
  wording.
- Recorded `confidence` values on these 16 clauses range from **0.193 to
  0.405** (verified by direct query) — i.e. within the same
  weak-zero-shot-confidence band the user has already flagged for this
  project. This is additional, independent evidence (not a coincidence)
  for the finding written up in full in `docs/NLP_EVALUATION.md`.

No changes were made to these records by this audit; they are left as
genuine (if low-confidence) pipeline output for demonstration purposes,
each already linked to its source `Upload` row and page number.

## 6. Genuine OCR test on real document content

The 3 real IPIDs (§4a) are digital PDFs, so the pipeline's vector-text path
was used and OCR was never invoked on them (confirmed: `used_ocr=false` for
all 3). To genuinely exercise Tesseract against real insurer content rather
than only synthetic images, page 1 of the real UNIQA document was
rasterised to a PNG at 200 DPI (`backend/scripts/evaluate_nlp.py`'s
`evaluate_real_ocr()`, reproducible on demand — not a static fixture) and
run through the real OCR path, with the same real PDF's own pdfminer text
as ground truth.

**Result: Tesseract mean confidence 92.6%; order-independent word-overlap
F1 0.982 (98.2% of individual words correctly recognised); but
character/word error rate 56%/69%.** These numbers are not contradictory —
full explanation and reproduction steps in `docs/NLP_EVALUATION.md` §"Real
OCR test": the source document uses a two-column "Was ist versichert? /
Was ist nicht versichert?" layout, and single-block OCR reads across both
columns line-by-line rather than column-by-column, which is a genuine,
disclosed document-layout-analysis limitation — not a character-recognition
failure, and not softened or hidden here.

## 7. Source clauses / provenance metadata fields generally

Every place in the `Policy` schema that has a dedicated provenance field
(`document_title`, `document_type`, `source_url`, `source_organisation`,
`retrieval_date`, `last_reviewed_date`) is still `NULL` for all 12
catalogue `Policy` rows, since the 3 real documents were deliberately
**not** forced into the `Policy` table (see below) — there is no
fabricated provenance metadata anywhere in the database. Where the schema
requires a non-nullable value with no honest source (e.g.
`Provider.rating_score`), the fix remains a uniform, clearly-placeholder
value rather than invented differentiation.

**Why the 3 real documents are `Upload`/`Clause` rows, not `Policy` rows:**
the `Policy` table requires a non-null `monthly_premium_eur`,
`annual_premium_eur`, and `coverage_limit_eur` — but a real IPID is a
legally standardized *qualitative* summary document and does not disclose
an exact premium or a fixed sum insured (those are set per-contract based
on individual risk; the documents themselves say "wie im
Versicherungsvertrag vereinbart" / "as agreed in the insurance contract").
Inventing a premium figure to satisfy the schema would be exactly the kind
of fabrication this phase forbids. The `Upload`/`Clause` path is the
architecturally correct, already-existing home for a real, priced-unknown
source document — it requires no schema change, carries no risk to the
recommendation/comparison scoring engine (which only reads `Policy` rows),
and every clause it produces is still fully traceable to both the real
`Upload` row and (via `MANIFEST.json`) the real source URL.

## 8. Source-document redistribution and database cleanup (final freeze)

**Redistribution decision**: the 3 real PDFs (and the page-1 PNG rasterised
from one of them) are **not committed to this repository**, even though
they are freely publicly accessible on each insurer's own website.
Redistribution permission for third-party copyrighted insurer PDFs is
unclear — free public accessibility is not the same as a licence to
re-host a copy in a separate public Git repository. Rather than guess,
the reproducibility chain is kept intact without redistributing the files:

- `backend/data/source_documents/MANIFEST.json` is committed (tracked via
  a `.gitignore` exception) and records, for each document: insurer,
  product name/line, document type/title/version date, the official
  source URL, the source page it was found on, retrieval date and method,
  document language, sha256 checksum, and byte size.
- `backend/scripts/download_source_documents.py` re-downloads each file
  from its recorded `source_url` and verifies the sha256 checksum matches
  what was recorded at first retrieval (2026-08-28), warning (not
  silently trusting) if an insurer has since revised the document.
- `backend/scripts/ingest_real_documents.py` and
  `backend/scripts/evaluate_nlp.py`'s `evaluate_real_ocr()` both now fail
  with a clear, actionable message (pointing at the download script)
  rather than crashing obscurely if the PDFs aren't present locally.
- The raw ingestion API responses (`_ingestion_results.json`, which embed
  the full real extracted clause text) are similarly not committed, for
  the same reason — the aggregate statistics that matter for the
  dissertation are in this document and in `docs/NLP_EVALUATION.md`.

**Database cleanup**: the development database's `uploads`/`clauses`
tables were audited row by row (see §4b) and 13 disposable QA-test rows
were deleted — repeated E2E-test-run duplicates and manually-generated
images that were never saved as reproducible fixtures. The 4 rows backing
this document's `VERIFIED_SOURCE`/`DOCUMENT_EXTRACTED` findings (uploads
15–18) were kept, along with all 15 providers and 12 demo policies.
**The submitted repository does not depend on this specific local
database's row IDs or content** — a fresh clone reconstructs an equivalent
state entirely from `alembic upgrade head`, `python -m scripts.seed`,
`python -m scripts.download_source_documents`, and
`python -m scripts.ingest_real_documents` (see `docs/RELEASE_CANDIDATE.md`
for the full reproduction sequence).

## Why no `VERIFIED_SOURCE` records existed before this update

*(Retained for the audit trail — no longer the current state; see §4a.)*
Populating `VERIFIED_SOURCE` policy/clause data honestly requires actually
retrieving a real, currently-published Austrian IPID or AVB document,
recording its exact source URL, title, version/date and retrieval date,
and transcribing (or running the real pipeline against) its actual clause
text. That had not been done as of the first version of this document. Per
the explicit instruction governing this audit — *"Never invent provenance.
If the origin of existing seeded data cannot be established, label it
Demo/Synthetic or Unknown"* — the honest action at the time was to leave
the catalogue as `DEMO_SYNTHETIC`/`DOCUMENT_EXTRACTED`-from-a-test-fixture
rather than backfill plausible-looking source URLs. That gap is now closed
for 3 documents (§4a); it remains true that the 12 `Policy` catalogue rows
are still `DEMO_SYNTHETIC` and that 9 of 15 providers have no associated
policy at all.

## Summary table

| Record type | Count | Classification |
|---|---|---|
| Providers — `name`, `logo_url` | 15 | Factual (real company, verified own-domain logo URL) |
| Providers — `rating_score` | 15 | `DEMO_SYNTHETIC` (uniform placeholder) |
| Policies (all fields) | 12 | `DEMO_SYNTHETIC` |
| Real official documents (Uploads, incl. the genuine OCR test) | 4 | `VERIFIED_SOURCE` (see §4a, MANIFEST.json) |
| Real clauses extracted from them | 148 | `DOCUMENT_EXTRACTED` from `VERIFIED_SOURCE` |
| Real hand-labelled clause examples (eval only) | 59 | `VERIFIED_SOURCE`-traceable, manually labelled |
| Synthetic-fixture uploads (historical — removed §4b/§8) | 0 (was 3) | Real files, synthetic test content |
| Clauses from synthetic-fixture uploads (historical — removed) | 0 (was 16) | `DOCUMENT_EXTRACTED` (real pipeline output on a synthetic fixture) |
| QA/test-debris uploads removed in the final freeze (§8) | 13 | Disposable — not evidence for any documented result |
| Derived per-document clause-type distribution table (§4a) | 30 cells | `DERIVED` from the 59 real labelled examples |
| `Policy.source_url`/`document_title`/etc. | 0 populated | N/A — the 3 real documents are Upload/Clause rows, not Policy rows (see §7) |
| `UNKNOWN` records | 0 | None — every record's origin above was established with confidence |
