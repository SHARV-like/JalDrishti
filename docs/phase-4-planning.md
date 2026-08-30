# Phase 4: intervention intelligence and planning

## Model and responsibilities

`recommendation_rulesets` stores organisation/region-specific, versioned weights and assumptions. Only Admin can create a ruleset. `recommendation_runs` stores immutable planning inputs, results, and the ruleset version; Admin, Supervisor, and Auditor can create scenarios. Every output is an estimate, never a guarantee, and requires field survey and engineering approval.

The six supported interventions are Contour Trench, Farm Pond, Check Dam, Percolation Tank, Recharge Pit, and Afforestation. Scores use configured weights with available slope, runoff, vegetation, terrain/soil proxy, drainage proximity, rainfall, existing coverage, and residual-risk inputs. Missing values use explicit pilot defaults and are shown as assumptions.

## APIs

- `POST /api/v1/planning/rulesets` — Admin only; validates weights and preserves a version.
- `POST /api/v1/planning/risk-zones/{id}/scenarios` — authorised scenario comparison with alternatives, factors, constraints, assumptions, and disclaimer.
- `GET /api/v1/planning/dashboard` — filtered organisation-scoped operational summary.

Dashboard filters accept watershed, village, intervention type/status, verification status, and risk level. The dashboard reports intervention progress, verification backlog, high-priority risk zones, pending alerts, and directs clients to observed environmental time series. Exports/reports should consume persisted `recommendation_runs`, retaining the source version and disclaimer.

## Limits

Rules are transparent planning heuristics, not hydrological or engineering designs. They do not replace site survey, land/consent checks, detailed soil studies, drainage validation, or engineering approval. Satellite/environmental observations must not be interpreted as automatic proof of intervention impact.
