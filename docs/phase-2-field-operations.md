# Phase 2: intervention and field operations

## Purpose

Phase 2 adds organisation-scoped operational records without replacing the SIH demo routes. All GeoProof, image-duplicate, and metadata checks are decision support. They create or preserve a review state; they do not establish fraud or causal impact.

## Production API

All routes require OIDC in production. Development test mode uses the existing membership-backed headers only when `APP_ENV` is not production.

| Route | Roles | Purpose |
| --- | --- | --- |
| `POST /api/v1/operations/villages` | Admin | Create a watershed-linked village. |
| `POST /api/v1/operations/risk-zones` | Admin | Add a validated high/moderate/low risk zone. |
| `POST /api/v1/production/interventions/{id}/evidence-intents` | Admin, Field Worker, Supervisor | Create a private storage upload intent. |
| `POST /api/v1/operations/evidence/{id}/complete` | Admin, Field Worker, Supervisor | Persist capture/GPS/device/hash metadata and transparent GeoProof factors. |
| `POST /api/v1/operations/interventions/{id}/submit` | Admin, Field Worker, Supervisor | Submit a completed or returned site for review. |
| `GET /api/v1/operations/reviews/queue` | Admin, Supervisor, Auditor | Read the role-appropriate Needs Review queue. |
| `POST /api/v1/operations/reviews/{id}` | Admin, Supervisor, Auditor | Approve, reject, or retain a review with comments. |

Evidence completion validates coordinate pairs and WGS84 bounds, GPS accuracy bounds, SHA-256 format, file constraints from the upload-intent route, and organisation ownership. A matching hash is a duplicate-review warning, not an automatic rejection.

## Operator workflow

1. Field Worker records a site and creates an upload intent.
2. Upload bytes directly to the configured private storage provider; do not send them to public URLs.
3. Complete the evidence record with metadata. Missing GPS, low score, poor accuracy, or duplicate hash keeps the item in `Needs Review`.
4. Submit Completed/returned interventions with a comment and optional reviewer assignment.
5. Supervisor or Auditor inspects factors/history and records an approval, rejection, or request for review. The result changes the intervention state and creates an audit event.

## Migration

Alembic revision `0002_field_operations` adds `villages`, `risk_zones`, `evidence_observations`, and `verification_reviews`, plus optional village/reviewer fields on interventions. It is additive and does not alter the demo compatibility endpoints.
