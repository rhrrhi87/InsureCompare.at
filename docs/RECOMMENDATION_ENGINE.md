# Explainable Recommendation Engine

## Model

`app/recommender/scorer.py` implements a weighted-additive scoring function
over five normalised features, each in `[0, 1]`:

```
S(policy, profile) = 0.25·f_price + 0.30·f_coverage + 0.20·f_exclusion
                    + 0.10·f_deductible + 0.15·f_fit
```

| Factor | Weight | What it measures |
|---|---|---|
| Coverage | 30% | Breadth of `coverage_items` vs. the user's preferred coverage level, plus overlap with `required_coverages` |
| Price | 25% | How the monthly premium compares to the user's budget (quadratic penalty once over budget) |
| Exclusion | 20% | How many/which exclusions overlap with what the user actually needs covered |
| Profile Fit | 15% | Product-line match + risk-tolerance vs. policy risk-level lookup table |
| Deductible | 10% | Distance from the user's preferred deductible bucket (low/medium/high) |

Weights are stored per-recommendation (`Recommendation.weights`) so a past
result's exact configuration is always reproducible, and can be overridden
per-request (`RecommendationRequest.weights`) or per-profile
(`RiskProfile.weights`, exposed in the dashboard's "Advanced scoring
weights" panel, which enforces the weights summing to 100% client-side
before allowing a save).

## Why no separate SHAP library is invoked

Because `S` is a linear (additive) function of the five feature values, the
per-feature *contribution* — `weight × feature_value` — is exactly the
Shapley value of that feature under any coalition ordering. This is a
direct consequence of the symmetry and dummy-player axioms of Shapley
values applied to an additive function: no sampling or coalition
enumeration (as `TreeSHAP`/`KernelSHAP` would require) is needed to get the
*exact* answer. `shap` remains a pinned dependency for
experimentation/comparison, but the production explanation panel uses the
closed-form contributions directly (`FeatureContribution.contribution` in
`app/schemas/recommendation.py`).

## What the UI shows

- **Best-match card**: total score (0–100), premium, per-factor breakdown
  (0–100 per factor), and a template-generated narrative sentence built
  from the actual computed feature values (never a canned string
  independent of the real score — see `Recommender._narrative`).
- **Ranked list**: same breakdown + each factor's weight, per policy.
- **Scoring methodology card**: the five weights currently in effect and
  what each factor means.
- **Policy detail → Source Evidence**: drills from a policy down to its
  backing `Clause` rows (page number, confidence, verbatim text) — empty
  and honestly labelled for demonstration-catalogue policies that have no
  attached source document (see `docs/DATA_SOURCES.md`).

## Determinism

Given the same policy data, profile, and weights, `Recommender.score()` is
a pure function — no randomness, no external calls — so the same inputs
always produce the same ranking and scores. This is exercised directly by
`backend/tests/test_recommender.py`.

## Known limitation

The five feature functions (`_f_price`, `_f_coverage`, etc.) are
hand-designed heuristics validated against a small informal expert-ranking
exercise during the original dissertation work, not a trained/calibrated
statistical model. This is disclosed rather than presented as a
machine-learned model, consistent with the "no fabricated AI results" rule.
