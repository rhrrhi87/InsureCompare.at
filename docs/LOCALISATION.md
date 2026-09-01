# Localisation (EN/DE)

## Architecture

InsureCompare.at follows a **language-independent domain model**: the
database and API never store or return UI copy — only stable concept
identifiers (enum values like `product_line=car`, or controlled-vocabulary
strings like `"Theft protection"`). The frontend maps those identifiers to
localised labels at render time using `react-i18next`.

```
Database concept            "deductible" (ClauseType enum value)
English label                Deductible
German (Austrian) label      Selbstbehalt
Original extracted clause    "Der Selbstbehalt beträgt EUR 300."  (never translated)
```

This means: **changing the UI language never changes stored data, scores,
rankings, or weights.** Only presentation copy changes. See
`docs/TRACEABILITY_MATRIX.md` for the requirement-to-test mapping that
verifies this.

## Where translations live

```
frontend/src/locales/
  en/  common.json  navigation.json  insurance.json  comparison.json
       recommendation.json  documents.json  auth.json  admin.json
       errors.json  home.json  dashboard.json
  de/  (same file set, same keys)
```

`frontend/src/i18n/config.ts` loads every namespace for both languages
eagerly at startup (no lazy backend fetch — the whole bundle is a few dozen
KB of JSON, not worth the complexity of async namespace loading for a
two-language prototype).

`frontend/src/lib/i18nInsurance.ts` holds small helpers that translate
domain values that are *not* simple enum labels:

- `productLinePair` / `productLineLabel` — `ProductLine` → `{en, at}` label
  pair (Austrian German term, e.g. `car` → "Kfz-Versicherung").
- `translateConcept` — controlled-vocabulary coverage/exclusion strings
  (e.g. `"Theft protection"` → "Diebstahlschutz"). Falls back to the
  original English string for any concept not yet in the translation table,
  so unmapped catalogue data never silently disappears from the UI.

## Language switcher

`components/layout/LanguageSwitcher.tsx` renders "EN | DE" in the main
navigation (visible on every page, public and authenticated). Selecting a
language calls `i18next.changeLanguage()`, which:

1. Updates every mounted `useTranslation()` consumer immediately (no reload).
2. Persists the choice to `localStorage` under `insurecompare.lang`
   (`i18next-browser-languagedetector`, `detection.caches: ["localStorage"]`),
   so it survives a refresh and works before login.

**Known limitation / scope decision**: the spec allows *also* persisting the
preference server-side on the user's profile for authenticated users
("may also be persisted"). This prototype only persists client-side
(localStorage). Adding a `User.locale` column and a
`PATCH /users/me` endpoint would close this gap; it is listed as future work
in the README rather than implemented, to keep the auth/user schema change
surface small this late in the project.

## Original-language preservation

Clause evidence (`Clause.text` / `ExtractedClauseOut.text`) is the literal
extracted text and is **never** translated, regenerated, or edited by the
localisation layer — the evidence viewer (`PolicyDetailPage`,
`UploadPage`) always renders it verbatim with `lang="de"` on the element,
regardless of the active UI language. Only the surrounding UI labels
(clause type badge, page number, confidence) are translated.

## Backend error messages

Domain error `detail` strings (raised by `DomainError` subclasses in
`app/core/exceptions.py`) are plain English by design — translating every
raised string at the exception-class level would require restructuring the
whole exception hierarchy around error codes, which was judged out of scope
for the remaining project time.

Instead, `frontend/src/api/client.ts::extractErrorMessage` maintains a
lookup table (`errors.json` → `backend.<exact English string>`) for the
error messages a user can actually trigger through the golden-path UI
(login, upload, compare, recommend, profile). Recognised messages are
translated; anything unrecognised is shown as-is in English rather than
replaced with a generic "something went wrong" — a readable English
fallback beats hiding the actual problem.

## What is NOT yet localised

- Backend error messages outside the table above (rare edge cases —
  malformed payloads, FastAPI's own 422 validation messages).
- Admin free-text fields the admin types themselves (provider names, policy
  descriptions, document titles) — these are user-authored content, not UI
  copy, and are shown as entered regardless of UI language.
