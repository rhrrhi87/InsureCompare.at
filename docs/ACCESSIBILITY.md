# Accessibility Review

File: `docs/ACCESSIBILITY.md`
Review date: 2026-08-28

## Compliance claim — stated precisely

**InsureCompare.at does not claim full WCAG 2.1 AA compliance.** What is
demonstrated below is: (1) zero violations from an automated axe-core scan
against a defined, non-exhaustive set of 9 real pages/states, tagged
`wcag2a`/`wcag2aa`/`wcag21a`/`wcag21aa`, and (2) a manual code-level review
of a smaller set of practical checks (keyboard nav, focus visibility,
headings, labels, language switching, responsive behaviour). Automated
tooling — axe-core's own documentation says this explicitly — catches
roughly 30-50% of WCAG success criteria; it cannot verify reading order,
whether alt text is *meaningful*, whether a keyboard trap exists in a
complex widget, or a real screen-reader's actual experience of the page.
None of that has been tested here with an actual screen reader (JAWS/NVDA/
VoiceOver). Treat this document as evidence of a good-faith, partially
automated pass — not a compliance certificate.

## Automated checks (axe-core via Playwright)

Method: `@axe-core/playwright`, `withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa"])`,
run against 9 real rendered pages (3 public, 4 authenticated user, 2 admin)
via `frontend/e2e/accessibility.spec.ts`. Reproduce with:

```bash
cd frontend
npm run e2e -- accessibility.spec.ts
```

Full machine-readable output: `frontend/axe-results.json`.

### Initial scan (before this review's fixes)

| Page | Violations found |
|---|---|
| Landing | 1 (`color-contrast`, serious) |
| Login | 1 (`color-contrast`, serious) |
| Register | 1 (`color-contrast`, serious) |
| Dashboard | 1 (`color-contrast`, serious) |
| Compare | 3 (`color-contrast` serious; `label` critical ×3 nodes; `select-name` critical) |
| Admin / Providers | 1 (`color-contrast`, serious) |

Root causes, all genuinely found (not hypothetical):

1. **`text-slate-400` (#94a3b8) used as a caption/hint text colour on white
   or near-white backgrounds** — measured contrast 2.35–2.56:1 against the
   required 4.5:1 for normal-size text. This was the single largest
   contributor, appearing in 18 places across the codebase (footer
   disclaimers, hint text, badges, the language switcher's inactive
   button).
2. **`text-green-600` (#16a34a)** used for premium/price highlighting —
   3.29:1, below 4.5:1.
3. **`text-amber-600` (#d97706)** used for the "low extraction confidence"
   warning on the upload page — 3.18:1, below 4.5:1 (and this one matters
   more than most: it is a *warning*, so poor contrast works directly
   against its purpose).
4. **The compare page's row-selection checkboxes had no accessible name at
   all** (`label`, critical) — a screen reader would announce them as bare,
   unidentified checkboxes with no indication of which policy each one
   selects.
5. **Two `<select>` elements (product-line filter on the Compare page and
   Admin Policies page) had a visually-adjacent `<label>` that was not
   programmatically associated** (`select-name`, critical — no `htmlFor`/
   `id` pairing), so the visible label text was invisible to the
   accessibility tree.
6. One further round after widening scan coverage to the Recommendations,
   Upload, and Admin Policies pages found: the same `bg-brand-50` card
   background made `text-slate-500` (4.37:1) fall just short of 4.5:1 for
   the Deductible-Preference selector's hint text when active; the upload
   page's hidden dropzone `<input type="file">` had no accessible name;
   the Admin Policies page had the same unassociated-label `<select>`
   pattern as Compare.

### Fixes applied

All of the above were fixed in this session, not merely documented:

- `text-slate-400` → `text-slate-500` for caption/hint text (18 call
  sites across `HomePage`, `components/ui`, `UploadPage`,
  `AdminPoliciesPage`, `AdminDashboardPage`, `AdminDocumentsPage`,
  `LanguageSwitcher`, `ProtectedLayout`/`PublicLayout` footers,
  `DashboardPage`, `RecommendationsPage`, `LoginPage`, `PolicyDetailPage`).
  Two genuinely decorative icon-fill colours (`UploadIcon`, `FileText` in
  `UploadPage.tsx`) were deliberately left unchanged — axe's
  `color-contrast` rule targets text, and icon-only decorative glyphs are
  a different (non-text) contrast criterion that was already passing.
- `text-green-600` → `text-green-700` (Compare page premium cells and
  summary stat, Dashboard weight-validity indicator).
- `text-amber-600` → `text-amber-700` (upload page low-confidence warning
  and error text).
- Compare-page checkboxes: added `aria-label={"Pick: " + policyName}` per
  row.
- Compare-page and Admin-Policies-page `<select>` filters: added matching
  `id`/`htmlFor` pairs so the existing visible label is now
  programmatically associated.
- Upload page's dropzone `<input type="file">`: added `aria-label`.
- Dashboard's Deductible-Preference hint text: now switches to
  `text-brand-700` (not `text-slate-500`) when its option is the active
  selection, since the active state's `bg-brand-50` card background made
  the default hint colour fall just under threshold.

**Result: 0 violations across all 9 scanned pages after fixes** (verified
by re-running the same automated scan — see `axe-results.json`).

### What the automated scan does *not* cover

- Any page/state not in the 9 scanned (e.g. individual admin document
  review rows, the audit log page, error/404 states, modal-like inline
  forms not opened during the scan).
- Screen-reader reading order and announcement quality — axe checks
  structural/ARIA correctness, not whether the experience *makes sense*
  read aloud.
- Keyboard-only operability beyond what axe's static analysis infers
  (e.g. it does not attempt every tab-order path through a multi-step
  form).
- Genuinely dynamic content timing (toast auto-dismiss, live regions).

## Manual checks

| Check | Result | Notes |
|---|---|---|
| Keyboard navigation | Spot-checked | Tab order through the login form, dashboard preference controls, and compare-page checkboxes follows visual/DOM order; no keyboard traps observed in these flows. Not exhaustively tested on every admin CRUD modal. |
| Focus visibility | Pass, verified in code | A single global rule in `src/styles/index.css` — `*:focus-visible { @apply outline-none ring-2 ring-brand-500 ring-offset-2 ring-offset-white; }` — applies a visible focus ring to every focusable element site-wide, rather than relying on per-component styling (which would be easy to miss on new components). |
| Semantic headings | One real defect found and fixed | `LoginPage.tsx` had its `<h1>` on the "InsureCompare.at" brand mark and the actual page-specific heading ("Welcome Back") as a plain `<p>` — inconsistent with `RegisterPage.tsx`, which correctly uses `<h1>` for its own page title ("Create your account"). Fixed by swapping the brand mark to a `<p>` and promoting "Welcome Back" to `<h1>`, matching the register page's pattern. This was caught via an E2E test locator failure (an `h1` role query didn't find the expected heading), not by visual inspection alone. |
| Form labels | Verified via axe + manual read | All text inputs across login/register/dashboard use `<Label htmlFor>` correctly (a pre-existing project pattern); the gaps found were specifically the two `<select>` filters and the compare checkboxes, listed above and fixed. |
| Alt text | N/A currently | The application renders **zero `<img>` elements** anywhere in `frontend/src` at review time — all icons are inline SVG components (`lucide-react`), which don't require `alt` text the way raster/`<img>` content does. `Provider.logo_url` (see `docs/DATA_PROVENANCE_AUDIT.md`) is stored as real data but is not currently rendered as an `<img>` anywhere in the UI — so there is no missing-alt-text risk today, but if/when provider logos are rendered in a future iteration, each must get a real, non-empty `alt` (the provider's name), not a decorative empty `alt=""`. |
| ARIA usage | Spot-checked, correct where present | `LanguageSwitcher` uses `role="group"`, `aria-pressed`, and `aria-hidden` on its decorative separator correctly. `components/ui/index.tsx`'s spinner/alert use `role="status"`/`role="alert"` correctly. No incorrect or redundant ARIA roles were found on the pages reviewed. |
| Colour contrast | Automated (see above) + spot manual check | All 9 scanned pages pass 4.5:1 for normal text after fixes. Not manually re-checked pixel-by-pixel outside the scanned pages. |
| Error messages | Spot-checked | Form validation errors (`errors.email.message`, etc.) render as visible red text adjacent to the relevant field, and are real Zod-schema-driven messages, not generic. They are not currently wired to `aria-describedby` on the input, so a screen reader encountering the input directly (rather than reading the page top-to-bottom) would not automatically hear the error — a real, disclosed gap, not fixed in this pass since it touches the shared `Input`/`Label` component contract across every form in the app and warranted a larger, separately-reviewed change than this pass's scope. |
| `lang` attribute | Pass, verified in code and by E2E test | `frontend/src/i18n/config.ts` registers a `languageChanged` listener that sets `document.documentElement.lang` to match the active i18next language; `frontend/e2e/journeys.spec.ts`'s language-switch test asserts `<html lang="de">` after switching, and it passes. |
| EN/DE switching | Pass | Verified both via the automated E2E test and via the manual browser session in the prior testing round (`docs/TESTING.md`). Switching language only swaps UI copy; it does not alter domain data, scores, or recommendations (by design — see the comment in `LanguageSwitcher.tsx`). |
| Responsive behaviour | Pass, verified in prior session (`docs/TESTING.md`) | No horizontal overflow at 375px width (iPhone SE/8 class) after the header nav-row fix documented in that file; not re-verified in this pass. |

## Known, disclosed gaps (not fixed in this pass)

- Form validation errors are not wired to `aria-describedby` (see table
  above) — a real accessibility gap for screen-reader users specifically,
  not a hypothetical one.
- No screen-reader software (JAWS/NVDA/VoiceOver) was used to verify the
  actual experience; all "manual" checks above are code-level/DOM-level
  reasoning plus keyboard spot-checks, not a screen-reader session.
- The automated scan covers 9 pages/states out of the full application
  surface (e.g. it does not cover the admin audit log, admin documents
  review detail, or every modal/dialog).
- No dedicated keyboard-trap test exists for any modal or multi-step
  admin form.

These gaps are the honest reason this document does not claim full WCAG
2.1 AA compliance, per the instruction governing this review.
