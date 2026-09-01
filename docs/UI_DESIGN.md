# UI Design

## Stack (unchanged from the original submission)

React 18 + TypeScript + Vite + Tailwind CSS, Zustand for client auth state,
TanStack Query for server state, React Router for routing, `react-i18next`
for localisation (new this phase — see `docs/LOCALISATION.md`).

The original design brief recommended shadcn/ui; the codebase instead has a
small hand-rolled Tailwind component set (`components/ui/index.tsx` +
`Button.tsx`: `Card`, `Badge`, `Alert`, `Spinner`, `Input`, `Select`,
`Label`, `StatCard`, `Button`). This was a deliberate decision **not** to
migrate: the existing kit is consistent, accessible-ish (icon+text status
indicators, not colour-only), and already used everywhere — a full shadcn/ui
migration this late in the project would be pure churn with no functional
benefit, and the project's own instructions say not to replace working
frontend architecture without a compelling reason.

## Visual language

Deep navy/brand-blue accents (`brand-*` Tailwind scale), white/neutral-gray
surfaces, green for positive coverage/status, amber/red for
warnings/exclusions — never colour alone (every status badge pairs colour
with text, and coverage/exclusion lists pair colour with a check/cross icon).

## Screens (persistent nav, card-based grouping — as originally specified)

**Public**: Home (hero, feature cards, insurance-type grid, "How it works"
4-step section, "Beyond price comparison" differentiation matrix, About,
disclaimer footer), Login, Register.

**Authenticated**: Dashboard (4 action cards + preferences form, including
the collapsible "Advanced scoring weights" panel and the required-coverages
picker), Upload (drag-and-drop + per-clause evidence preview), Compare (2–3
policy picker, side-by-side table, summary stats), Recommendations
(best-match hero, ranked list, scoring-methodology card), Policy Detail
(coverage/exclusions/summary + Source Evidence section).

**Admin** (`AdminLayout` tab bar: Dashboard / Providers / Policies /
Documents / Audit): KPI overview, provider CRUD, policy CRUD with
retire/reactivate (never delete), document/upload review with OCR
confidence flags, full audit log.

## Comparison table

Capped at 3 policies (enforced both client-side, in `ComparePage`'s
selection logic, and server-side, in `CompareService`/`CompareRequest`
validation) — not increased, per the original spec's usability rationale.
Wide tables scroll horizontally inside their own container rather than
squeezing columns on small screens.

## Accessibility

- Semantic headings, labelled form controls (`<Label htmlFor>`), visible
  focus rings on interactive elements (`focus-visible:ring-2` on `Button`).
- Every status/risk/coverage indicator combines colour with text or an
  icon — never colour alone.
- `Spinner` exposes `role="status"` and a localised `aria-label`.
- Language switcher is a `role="group"` of buttons with `aria-pressed`.

A full WCAG 2.1 AA audit (contrast ratios measured, keyboard-only pass,
screen-reader pass) has not been run in this session — see
`docs/TESTING.md` for what has and hasn't been executed.
