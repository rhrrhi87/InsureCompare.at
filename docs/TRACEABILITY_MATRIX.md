# Traceability Matrix

Requirement → Implementation → Test → Evidence. Rows are the major
functional requirements from the project specification; see
`docs/IMPLEMENTATION_PLAN.md` for the full gap analysis this was derived
from.

| # | Requirement | Implementation | Test | Evidence |
|---|---|---|---|---|
| 1 | Bilingual EN/DE UI, live switch, no reload | `frontend/src/i18n/`, `locales/{en,de}/*.json`, `LanguageSwitcher.tsx` | Manual verification (see `docs/TESTING.md` — automated test not yet written) | `docs/LOCALISATION.md` |
| 2 | Language switch never changes stored data/scores | Language-independent domain model: API returns stable ids, frontend maps to labels | Architectural guarantee; automated regression test listed as TODO in `docs/TESTING.md` | `docs/LOCALISATION.md` |
| 3 | Original (German) source clause preserved verbatim | `Clause.text` never rewritten; evidence viewer renders with `lang="de"`, never runs it through `t()` | Manual code review | `PolicyDetailPage.tsx`, `UploadPage.tsx` |
| 4 | Austrian terminology (Kfz-/Haushalts-/Reise-/Rechtsschutzversicherung, Selbstbehalt, etc.) | `locales/de/insurance.json` | Manual review against spec §7 glossary | `insurance.json` |
| 5 | 5-factor weighted scoring (Coverage 30/Price 25/Exclusion 20/Fit 15/Deductible 10) | `app/recommender/scorer.py::DEFAULT_WEIGHTS` | `test_recommender.py::test_default_weights_sum_to_one` etc. | `docs/RECOMMENDATION_ENGINE.md` |
| 6 | Per-factor weight/sub-score/contribution shown, matches actual score | `RecommendationsPage.tsx` (breakdown, contributions, methodology card) | `test_recommendation_api.py::test_recommend_returns_ranked_policies` (asserts contributions present) | `docs/RECOMMENDATION_ENGINE.md` |
| 7 | User-adjustable weights, must sum to 100% | `DashboardPage.tsx` advanced panel; `RiskProfile.weights` | Manual UI review; backend accepts arbitrary weights and normalises (`normalise_weights`) | `WEIGHTS_CHANGED` audit test |
| 8 | Evidence traceability: recommendation → factor → clause → page → document | `PolicyDetailPage.tsx` Source Evidence section, `Clause` model, `/policies/{id}/clauses` | `test_admin_catalogue.py::test_policy_clauses_endpoint_empty_for_demo_catalogue` | `docs/DATA_SOURCES.md` (honest empty-state for demo data) |
| 9 | Document upload: PDF/JPEG/PNG, 10MB cap, OCR+NLP pipeline | `UploadService.ingest`, `app/nlp/ocr.py`, `app/nlp/extractor.py` | `test_nlp.py` (pipeline units); no upload-endpoint integration test yet (see `docs/TESTING.md`) | `docs/AI_PIPELINE.md` |
| 10 | Low-confidence extraction shown honestly, not hidden | `UploadPage.tsx` clause list warning, `OCR_CONFIDENCE_THRESHOLD` | Manual review | `docs/AI_PIPELINE.md` |
| 11 | Clause taxonomy incl. Deductible/Obligation/Territorial Scope/Duration/Optional Benefit | `app/db/enums.py::ClauseType` | `test_nlp.py::test_classifies_deductible_clause`, `test_classifies_territorial_scope_clause` | `docs/AI_PIPELINE.md` |
| 12 | Max 3-policy comparison | `ComparePage.tsx` selection cap; `CompareService`/`CompareRequest` (`min_length=2, max_length=3`) | `test_recommendation_api.py::test_compare_endpoint` | `docs/UI_DESIGN.md` |
| 13 | Admin: manage providers/policies, never hard-delete | `PolicyService.retire_policy/reactivate_policy/set_provider_active`; `AdminProvidersPage.tsx`, `AdminPoliciesPage.tsx` | `test_admin_catalogue.py::test_retire_policy_hides_it_from_default_listing`, `test_retire_requires_admin` | `docs/DATABASE.md` |
| 14 | Admin: review document/extraction status | `AdminDocumentsPage.tsx`, `GET /admin/uploads` | Manual review (no dedicated test yet) | — |
| 15 | Audit log: LOGIN/UPLOAD_PROCESSED/RECOMMENDATION_GENERATED/POLICY_CREATED/UPDATED/RETIRED/WEIGHTS_CHANGED | `AdminService.record_action`, wired into `auth.py`, `documents.py`, `recommendations.py`, `policies.py`, `profiles.py` | `test_admin_catalogue.py::test_policy_create_and_retire_are_audited`, `test_login_and_recommendation_are_audited`, `test_changing_scoring_weights_is_audited` | `docs/SECURITY.md` |
| 16 | Session revocation (refresh-token rotation, logout) | `sessions` table, `SessionService`, `/auth/refresh` rotation, `/auth/logout` | `test_auth.py::test_refresh_rotates_and_invalidates_old_token`, `test_logout_revokes_the_refresh_token` | `docs/SECURITY.md` |
| 17 | No fabricated live premiums / competitor claims | `is_demo_data` flag + "Demonstration data" badge; homepage matrix uses "Conventional comparison approach", never names a competitor | Manual review | `docs/DATA_SOURCES.md` |
| 18 | Disclaimer shown | `common.json::footer.disclaimer`, rendered in `PublicLayout.tsx` and `ProtectedLayout.tsx` | Manual review | — |
| 19 | "Beyond price comparison" / differentiation section | `HomePage.tsx` `#why` section + matrix | Manual review | `home.json` |
| 20 | "How it works" 4-step section mapped to real functionality | `HomePage.tsx` `#how-it-works` | Manual review | `home.json` |

## What this matrix does not yet cover

Performance benchmarking, a WCAG accessibility audit, and NLP
precision/recall metrics are documented as explicit gaps in
`docs/TESTING.md` rather than rows here with fabricated results.
