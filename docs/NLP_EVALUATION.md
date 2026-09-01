# NLP / OCR Evaluation

File: `docs/NLP_EVALUATION.md`
Evaluation date: 2026-08-28 (updated same day with real-document results)
Evaluation script: `backend/scripts/evaluate_nlp.py` (reproducible — run
`python -m scripts.evaluate_nlp` from `backend/` with the project venv
active and the backend's own dev server not required; raw machine-readable
output is written to `backend/scripts/nlp_evaluation_results.json`)

## Research claim boundary

This document validates **document understanding** — ingestion, PDF text
extraction, OCR, clause extraction, and clause classification — against
real official Austrian insurance documents. It does **not** validate, and
must not be read as validating, the comparison/recommendation catalogue's
pricing: that catalogue still uses `DEMO_SYNTHETIC` policy and pricing data
where authoritative comparable pricing was unavailable (real IPIDs do not
disclose it — see `docs/DATA_PROVENANCE_AUDIT.md` §7). Do not describe this
project as one where "recommendations are based entirely on live/real
insurer quotations" or where "InsureCompare currently compares live
Austrian insurance prices" — neither is true. The accurate description is:
the prototype evaluates document understanding on real official Austrian
insurance documents, while controlled synthetic policy and pricing data is
used for parts of the comparison and recommendation demonstration where
authoritative comparable pricing is unavailable.

## Headline finding — stated plainly, as required

**On REAL official Austrian insurer documents, the zero-shot clause
classifier measured 32.2% accuracy / 0.226 macro-F1, and the keyword
fallback classifier measured 55.9% accuracy / 0.490 macro-F1 — both
markedly worse than either classifier's own score on the project's earlier
synthetic/controlled evaluation set (40.0%/70.0% respectively).** This gap
is itself an important, honest finding: performance measured on
hand-authored synthetic sentences overestimates real-world performance,
because synthetic sentences were written using the same vocabulary the
extractor already targets. **Neither classifier is production-ready on
real documents, and this is not softened below.**

**A genuine OCR test against a real, rasterised IPID page** (not a
synthetic image) found Tesseract's character-level recognition to be
strong (92.6% mean confidence, 98.2% order-independent word-overlap F1)
but its effective word/character error rate to be very high (69%/56%)
because the source document's two-column layout defeats single-block OCR's
reading order — a genuine, disclosed document-layout-analysis limitation,
not a character-recognition failure. Full detail in §3 below.

## What was evaluated — two categories, clearly distinguished throughout

**Category A — controlled/synthetic** (built when the project had no real
source documents; kept for continuity and because it still measures
something real: the pipeline's actual behaviour, just on artificial input):

| File | Purpose | N |
|---|---|---|
| `clause_classification_dataset.json` | 10-class clause-type classification | 60 (6 per class) |
| `extraction_dataset.json` | Numeric field extraction (premium/deductible/limit) | 24 |
| `vocabulary_extraction_dataset.json` | Coverage/exclusion vocabulary matching | 8 |
| Two PIL-rendered PNG images | OCR-only measurement | — |

**Category B — REAL official documents**, downloaded directly from 3
Austrian insurers' own domains (full source URLs, retrieval dates, and
document versions in `backend/data/source_documents/MANIFEST.json`;
classified `VERIFIED_SOURCE` in `docs/DATA_PROVENANCE_AUDIT.md` §4a):

| Document | Insurer | Product line |
|---|---|---|
| `uniqa_kfz_haftpflicht_ipid.pdf` | UNIQA Österreich Versicherungen AG | Car (Kfz-Haftpflicht) |
| `generali_haushalt_ipid.pdf` | Generali Versicherung AG | Household |
| `wienerstaedtische_rechtsschutz_ipid.pdf` | WIENER STÄDTISCHE Versicherung AG – VIG | Legal |

From these, `real_clause_classification_dataset.json` (59 examples)
hand-labels real sentences reconstructed verbatim from each document's own
text (IPIDs are terse, bulleted documents — reconstructing a grammatical
sentence from a bullet and its own lead-in, e.g. "X Nuklearschäden" under
"Was ist nicht versichert?" → "Nicht versichert sind Nuklearschäden.",
adds no new content). Every example records which real document it came
from. No `definition`-class example exists in any of the 3 real
documents — an honest property of the IPID format, not a labelling gap.

Nothing in Category B is fabricated: every source URL, sentence, and OCR
ground-truth string traces to a real, currently-published document.

## 1. Clause classification — real vs. synthetic, side by side

| | Synthetic (60 examples) | **Real (59 examples)** |
|---|---|---|
| Keyword fallback — accuracy | 0.700 | **0.559** |
| Keyword fallback — macro F1 | 0.715 | **0.490** |
| Zero-shot gBERT — accuracy | 0.400 | **0.322** |
| Zero-shot gBERT — macro F1 | 0.361 | **0.226** |

Both classifiers are weaker on real text than on the synthetic set they
were partly validated against — exactly the generalisation gap a rigorous
evaluation should surface rather than hide behind a single flattering
number.

### 1a. Real-document per-class results — keyword fallback

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| coverage | 0.545 | 0.600 | 0.571 | 10 |
| exclusion | 0.944 | 1.000 | 0.971 | 17 |
| limit | 0.600 | 0.750 | 0.667 | 4 |
| deductible | 1.000 | 1.000 | 1.000 | 1 |
| **obligation** | **0.000** | **0.000** | **0.000** | **12** |
| definition | — | — | — | 0 (no real examples exist) |
| territorial_scope | 1.000 | 0.500 | 0.667 | 6 |
| duration | 0.333 | 0.200 | 0.250 | 5 |
| optional_benefit | 1.000 | 0.500 | 0.667 | 2 |
| other | 0.059 | 0.500 | 0.105 | 2 |

**The keyword classifier completely fails on real `obligation` clauses**
(0.000 F1 on 12 real examples) — the confusion matrix
(`nlp_evaluation_results.json`) shows 10 of 12 real obligation sentences
misclassified as `other`. Real obligation phrasing in these IPIDs ("ist …
zu melden", "ist mitzuwirken", passive-voice duty constructions) does not
match the keyword list built from the synthetic sentences' own more
direct phrasing ("Der Versicherungsnehmer ist verpflichtet…"). This is a
concrete, real sim-to-real gap, not a synthetic-data artefact.

### 1b. Real-document per-class results — zero-shot gBERT

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| **coverage** | **0.000** | **0.000** | **0.000** | **10** |
| exclusion | 1.000 | 0.176 | 0.300 | 17 |
| limit | 0.250 | 1.000 | 0.400 | 4 |
| deductible | 0.000 | 0.000 | 0.000 | 1 |
| obligation | 0.368 | 0.583 | 0.452 | 12 |
| definition | — | — | — | 0 |
| territorial_scope | 0.667 | 0.333 | 0.444 | 6 |
| duration | 0.750 | 0.600 | 0.667 | 5 |
| optional_benefit | 0.000 | 0.000 | 0.000 | 2 |
| other | 0.000 | 0.000 | 0.000 | 2 |

**All 10 real `coverage` examples were misclassified — 10 of 10 predicted
as `obligation`.** Real IPID coverage sentences ("Versichert ist die
Bezahlung von gerechtfertigten Schadenersatzansprüchen…") are long,
formal, and structurally resemble the model's idea of an obligation
statement more than the shorter synthetic coverage sentences did. This is
the single clearest real-document failure mode found.

Full confusion matrices for both classifiers, both datasets: see
`backend/scripts/nlp_evaluation_results.json` (`clause_classification_real`
key).

### Why both classifiers weaken on real text

1. **The keyword vocabulary was built to match phrasing patterns the
   project itself invented** for the synthetic dataset. Real IPID prose
   uses different, more formal/legalistic constructions for the same
   underlying concepts (see the `obligation` example above) — the
   vocabulary simply doesn't cover them.
2. **The zero-shot model's failure mode changed, not just its score.** On
   synthetic data its weakest classes were `exclusion`/`deductible`/`other`;
   on real data its single worst failure is `coverage` — the model's
   confusion pattern is data-dependent, which argues against trusting a
   synthetic-only evaluation as representative.
3. **Real IPID sentences are longer and more clause-dense** than the
   deliberately clean synthetic sentences, and a single reconstructed
   sentence sometimes bundles a coverage statement with a scope qualifier
   or condition — genuine ambiguity a 10-way single-label classifier
   cannot represent well.

### Future improvements (updated with real-data evidence)

- Expand the keyword vocabulary using real obligation/duty phrasing
  patterns found in this and future real documents (a concrete, scoped
  task now that real failure examples exist to build from).
- Fine-tune a small German transformer on a larger labelled set built from
  more real documents — the 59-example real set here is sized to
  *measure*, not to *train*.
- Tune zero-shot hypothesis templates specifically against the `coverage`
  failure mode found on real data.
- The earlier recommendation to combine keyword-first with zero-shot
  fallback stands, and real data now shows it would help even more: the
  keyword classifier's real-data macro F1 (0.490) is more than double the
  zero-shot model's (0.226).

## 2. Numeric field extraction and vocabulary matching (synthetic only)

Unchanged from the synthetic evaluation — both are regex/lookup-based (not
learned models), evaluated against sentences built to match their exact
expected input shapes:

| Field | Accuracy | N |
|---|---|---|
| monthly_premium_eur | 1.000 | 4 |
| annual_premium_eur | 1.000 | 4 |
| deductible_eur | 1.000 | 8 |
| coverage_limit_eur | 1.000 | 8 |

Vocabulary matching (coverage/exclusion): precision 0.947, recall 1.000,
F1 0.973 (8 examples; one false positive, detailed in the script's raw
output).

**These were deliberately not re-evaluated against the real documents**:
none of the 3 real IPIDs disclose a specific premium, deductible, or
coverage-limit figure in EUR (see `docs/DATA_PROVENANCE_AUDIT.md` §7 for
why) — the regex extractor has nothing to extract in real IPID text by
design of the source document, not a bug. This is itself a finding: a
production system relying on this extractor to price real documents would
find IPIDs simply don't carry that information; only the fuller policy
wording (AVB) or an actual quote would.

## 3. OCR — synthetic vs. a genuine test on real content

### 3a. Synthetic (PIL-rendered, exact known ground truth)

| Case | Font size | Tesseract mean confidence | CER | WER |
|---|---|---|---|---|
| Clean, large font | 28pt | 94.1 | 0.000 | 0.000 |
| Small font | 14pt | 85.1 | 0.008 | 0.077 |

### 3b. REAL document (genuine OCR test)

Page 1 of the real UNIQA PDF was rasterised to a PNG at 200 DPI
(`evaluate_real_ocr()` in `evaluate_nlp.py`, done fresh at evaluation
time — not a static fixture) and run through the real Tesseract path.
Ground truth is that same real PDF's own pdfminer-extracted text for page
1 — i.e. both OCR output and ground truth come from the identical real
document, just two different real extraction methods.

| Metric | Value |
|---|---|
| Tesseract mean confidence | **92.6%** |
| Character Error Rate | 0.562 |
| Word Error Rate | 0.690 |
| Order-independent word-overlap precision | 0.974 |
| Order-independent word-overlap recall | 0.991 |
| Order-independent word-overlap F1 | **0.982** |

**These numbers are not contradictory, and the explanation matters more
than either single number:** the UNIQA IPID uses a two-column "Was ist
versichert? / Was ist nicht versichert?" layout. Tesseract was run with
`--psm 6` (treat the image as one uniform block of text), which reads
across both columns line-by-line rather than column-by-column — so
individual words are recognised correctly (98.2% word-overlap F1,
consistent with the 92.6% confidence) but end up in the wrong sequence,
which both CER and WER penalise heavily even though nothing was actually
misread. **This is a genuine, disclosed document-layout-analysis
limitation of using single-block OCR on a multi-column real document — not
a character-recognition failure**, and reporting only the WER/CER without
this explanation would have been actively misleading.

**What this means in practice:** this pipeline's OCR step, unmodified,
would garble the reading order of any real multi-column insurance document
(IPIDs commonly use this layout). A production fix would use a
layout-aware OCR mode (e.g. Tesseract `--psm 3`/`4` with column detection,
or a dedicated layout-analysis library) rather than single-block PSM 6 —
a concrete, scoped future-work item this real test directly motivates.

## Summary — what these numbers do and do not support

- **Do not claim** either clause classifier is production-ready — the
  measured real-document accuracy (55.9% keyword, 32.2% zero-shot) does
  not support that, and is materially worse than the already-modest
  synthetic-only numbers.
- **Do not claim** the numeric/vocabulary extractors have been validated
  against real documents — they haven't; real IPIDs don't contain the
  numeric data they look for.
- **Do not claim** OCR is reliable on real multi-column documents — the
  genuine test shows character recognition is strong but reading order
  breaks down, which is disclosed rather than hidden behind a single
  number.
- **Do claim**, with real evidence: the keyword fallback classifier
  meaningfully outperforms the zero-shot model on both synthetic and real
  data, and the gap is even larger on real data (0.490 vs. 0.226 macro
  F1) — a clear, actionable finding for anyone continuing this project.
- **Do claim**: this evaluation methodology itself — measuring on both
  controlled and real data and reporting the gap between them — is more
  honest than either measuring only on synthetic data (which this project
  did first) or skipping evaluation because no real data existed (which
  would have hidden the true accuracy entirely).
