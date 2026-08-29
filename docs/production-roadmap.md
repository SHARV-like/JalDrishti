# JalDrishti AI production roadmap

## Purpose and non-negotiables

JalDrishti will evolve from its working single-watershed MVP into a secure, multi-organisation watershed-intelligence platform. Existing demo GeoJSON layers, local evidence inspection, explainable GeoProof, controlled visual assessment, satellite comparison, recommendation logic, and PDF export remain supported as an offline/demo mode throughout the migration.

Production indicators must retain provenance and uncertainty. GeoProof is an evidence-review aid, not fraud-proof verification. Satellite change indicators are observed associations, not causal impact claims. Final intervention selection remains subject to field survey and engineering approval.

## Current baseline and Phase 1 gate

The repository already contains the first safe foundation commit (`286b785`): an Alembic migration that enables PostGIS on PostgreSQL, organisation and membership records, all five roles, auditable intervention transitions, a private-object-key upload-intent abstraction, OIDC issuer/audience validation, and an idempotent importer for the committed demo GeoJSON. The legacy FastAPI routes and React dashboard remain intact for the SIH demonstration.

Phase 1 does **not** create a cloud database, identity tenant, storage bucket, domain, or deployment. Those actions require a separate provider/cost/account/environment-variable review and explicit approval. The remaining Phase 1 hardening work is limited to repository code and documentation: formal architecture, deployment configuration templates, error/rate-limit policy, and integration-test coverage against a disposable PostGIS service.

## Proposed technology decisions

| Area | Decision | Reason |
| --- | --- | --- |
| API | Retain FastAPI; add SQLAlchemy 2, Alembic, Pydantic settings, and structured domain routers | Preserves MVP services while adding safe persistence and migrations. |
| Database | PostgreSQL 16 with PostGIS | Supports organisation isolation, relational workflow data, spatial boundaries, proximity, and spatial indexes. |
| Identity | Managed OIDC provider (Supabase Auth or equivalent) with JWT validation in FastAPI | Avoids custom password storage; supports secure sign-in and organisation membership. |
| File storage | S3-compatible object storage with private buckets and short-lived signed URLs | Keeps images and reports out of PostgreSQL and supports retention controls. |
| Web app | Retain React/Vite initially; add React Router, typed API client, TanStack Query, and service worker draft queue | Incremental path that preserves the current dashboard. |
| Geospatial processing | PostGIS for query/filtering; GeoPandas/Shapely workers only for heavier imports and analysis | Keeps routine spatial queries in the database and isolates expensive jobs. |
| Background work | Worker queue (Celery/RQ or managed queue) for imagery acquisition, reports, duplicate detection, and alerts | Keeps API requests bounded and observable. |
| Observability | OpenTelemetry traces, structured JSON logs, metrics, error reporting, and immutable audit events | Provides operational and audit visibility without leaking evidence data. |

## Target data model

Every tenant-owned table contains `organisation_id`, creation/update metadata, and a row-level access policy. UUIDs are public identifiers; database primary keys are not exposed.

| Domain | Core entities |
| --- | --- |
| Identity and tenancy | `organisations`, `users`, `memberships`, `roles`, `permission_grants`, `audit_events` |
| Geography | `watersheds`, `villages`, `drainage_features`, `risk_zones`, `spatial_sources`, `import_jobs` |
| Operations | `interventions`, `intervention_events`, `lifecycle_transitions`, `review_assignments`, `field_drafts` |
| Evidence | `evidence_items`, `evidence_files`, `exif_observations`, `gps_observations`, `duplicate_candidates`, `evidence_reviews`, `evidence_history` |
| GeoProof | `geoproof_runs`, `geoproof_factors`, `geoproof_rulesets`, `boundary_checks`, `proximity_checks` |
| Monitoring | `imagery_acquisitions`, `weather_observations`, `satellite_observations`, `change_runs`, `watershed_time_series`, `alerts` |
| Intelligence and reporting | `recommendation_rulesets`, `recommendation_runs`, `scenario_runs`, `report_jobs`, `export_jobs`, `data_attributions` |
| Governance | `consent_records`, `retention_policies`, `deletion_requests`, `data_exports` |

Spatial columns use SRID 4326 for source geometry, with appropriate projected calculations or PostGIS geography types for metre-distance checks. Geometry validation, source, acquisition time, uncertainty, processing method, and `data_status` are stored beside every spatial/derived record.

## API design

Version production APIs under `/api/v1`; preserve current MVP demo routes behind a documented `demo` mode until migration is verified.

- Identity: `GET /me`, organisation switch, membership/role administration; JWT required except health/readiness.
- Watersheds: filtered list/detail, PostGIS boundary read/write, import validation, source attribution.
- Interventions: create/read/update with lifecycle transitions only through permissioned transition endpoints.
- Evidence: create upload intent, direct-to-object-storage upload, submit/inspect/review/history endpoints; never proxy large production files through API memory.
- GeoProof: immutable run creation, factor breakdown, review decision, rule-version reference.
- Monitoring: provider acquisition records, observations, alerts, manual/preprocessed fallback ingestion.
- Intelligence: versioned ruleset retrieval, recommendation run, alternatives, constraints; scenario endpoints deferred until Phase 4.
- Operations: filterable queues, programme dashboards, reports, exports/imports, auditable job status.

Use Pydantic request/response schemas, pagination, cursor-safe sort/filter validation, idempotency keys for uploads/submissions, RFC 7807-style error responses, and OpenAPI examples that contain only synthetic data.

## Security and privacy plan

- OIDC login, short-lived access tokens, refresh-token rotation handled by the identity provider, and audience/issuer/JWK validation in the API.
- RBAC: Admin manages organisation and policy; Field Worker creates assigned drafts/evidence; Supervisor manages assignments and lifecycle; Auditor reads evidence/history/audit logs; Viewer has read-only scoped access.
- Organisation scoping is enforced in API queries and PostgreSQL row-level security as defence in depth.
- Private object storage with encrypted-at-rest files, server-side MIME/size/content validation, malware scanning hook, signed URLs, and content-disposition controls.
- Evidence EXIF is minimised in exports; exact GPS and personally identifying fields obey organisation policy and consent.
- Immutable, append-only audit events record security, lifecycle, review, export, and administrative actions without storing raw image bytes.
- Rate limits apply to auth-adjacent, upload-intent, inspection, export, and expensive spatial/monitoring endpoints.
- Secrets live only in the deployment secret manager; `.env.example` documents names but contains no values.

## Phases

### Phase 0 — Architecture and production foundations (1–2 weeks)

Deliverables: environment/settings model, container/dev compose, database provisioning guide, object-storage abstraction, architecture decision records, threat model, and CI baseline.

Acceptance criteria:

- Local production-like stack can start with non-secret example configuration.
- No production credentials are committed or required for unit tests.
- CI runs formatting/linting, type/build checks, unit tests, dependency audit, and secret scanning.

### Phase 1 — Secure operational foundation (3–5 weeks)

Scope: PostgreSQL/PostGIS schema and Alembic migrations; organisation/workspace model; JWT identity integration and RBAC; intervention records/lifecycle; private evidence upload intent and metadata persistence; safe import of current MVP data; audit events.

Migration: import `data/geo/*.geojson` and `data/geo/intervention-site-details.json` as one clearly labelled demo organisation through an idempotent command. Keep SVG/satellite assets as seeded demo storage objects with attribution. Existing public demo routes remain read-only during a compatibility window.

Acceptance criteria:

- Admin, Field Worker, Supervisor, Auditor, and Viewer permissions are covered by automated tests.
- Two organisations cannot read or mutate one another’s records, including via spatial filters and signed-file URLs.
- Intervention state transitions enforce `Planned → In Progress → Completed → Submitted → Verified / Needs Review` and record actor/time/reason.
- Evidence files reside in object storage; database stores metadata, checksums, keys, and review state only.
- Existing demo watershed, interventions, and assets migrate idempotently and reconcile by source ID/count/geometry validity.
- Current MVP demo experience continues to run from seeded data or its compatibility adapter.

### Phase 2 — Evidence review and stronger GeoProof (3–4 weeks)

Scope: GPS accuracy and timestamp checks, boundary/proximity factors, perceptual duplicate candidates, metadata consistency, review queue, evidence history, ruleset versioning, and reviewer decisions.

Acceptance criteria:

- Every factor has a plain-language explanation, input values, ruleset version, and outcome.
- Duplicate checks create review candidates rather than automatic fraud findings.
- Review decisions are auditable, reversible through a new decision event, and organisation-scoped.

### Phase 3 — Monitoring and observed indicators (5–7 weeks)

Scope: provider-adapter contracts for Sentinel/Landsat and rainfall/weather, acquisition catalog, cloud/quality checks, scheduled jobs, manual/preprocessed fallback, time series, change runs, and alerts.

Acceptance criteria:

- Providers can be enabled/disabled without changing dashboard business logic.
- Every observation records provider, acquisition time, cloud/quality value, method, geometry, and attribution.
- UI distinguishes observed change from causal impact and clearly presents fallback/demo data.

### Phase 4 — Intervention intelligence and planning (4–6 weeks)

Scope: configurable rule/weight system for contour trench, farm pond, check dam, percolation tank, recharge pit, and afforestation; constraints, alternatives, implementation priority, assumptions, and engineer review. Scenario/what-if planning follows only after rule validation.

Acceptance criteria:

- Rulesets are versioned, reviewable, testable, and cannot silently change historic recommendations.
- Each recommendation shows inputs, alternatives, constraints, score reasons, and engineering disclaimer.
- Scenario runs are clearly segregated from approved operational recommendations.

### Phase 5 — Operations, reporting, and governance (4–6 weeks)

Scope: programme and backlog dashboards, filters, branded PDF/XLSX reports, import/export APIs, attribution, retention schedules, consent controls, backup/recovery runbooks, and operator console.

Acceptance criteria:

- Filters cover watershed, village, intervention type, date, status, and risk with organisation scoping.
- Exports respect role, consent, retention, and audit policy.
- Backup restore and data-deletion exercises are documented and tested in a non-production environment.

## Testing strategy

| Layer | Coverage |
| --- | --- |
| Unit | GeoProof/recommendation rules, state machine, permission evaluator, file validation, schema validators. |
| Integration | PostGIS queries/RLS, object-storage signing, JWT validation, Alembic upgrade/downgrade, queue jobs, provider adapters. |
| Contract | OpenAPI schemas, compatibility adapter, provider payload fixtures, export schemas. |
| End-to-end | Login/organisation switching, field draft/offline sync, evidence submission/review, map filters, report/export, key role journeys. |
| Security | Dependency/secret scanning, SAST, rate-limit tests, tenancy-escape tests, signed URL expiry, upload attack fixtures. |
| Reliability | Migration reconciliation, job retry/idempotency, backup restore, manual-fallback and provider-outage drills. |

## Migration and rollout plan

1. Inventory and checksum current demo data; freeze source fixtures as migration test inputs.
2. Introduce database schema without changing the MVP UI; run read-only parity checks against GeoJSON.
3. Import seeded demo organisation idempotently; validate counts, IDs, geometry, attribution, and render parity.
4. Add compatibility read endpoints so the current UI can move from files to API one surface at a time.
5. Enable production workflows only for pilot organisations behind feature flags; retain manual/preprocessed satellite fallback.
6. Monitor audit, error, latency, queue, and tenancy-isolation signals; define rollback to read-only/demo mode.

## Estimated programme effort

The phased estimate is 20–30 engineering weeks for a small cross-functional team, excluding procurement, data-provider licensing, external security review, and field validation. Phase 1 is the recommended next approval gate and is estimated at 3–5 weeks.

## Phase 1 implementation checklist after approval

- Add configuration, local compose/dev services, Alembic, SQLAlchemy models, PostGIS migration, and seeded demo migration command.
- Add identity/JWT middleware and permission policy with test fixtures; document OIDC provider setup without secrets.
- Add organisation-scoped intervention CRUD/lifecycle and audit-event service.
- Add secure evidence upload-intent/storage abstraction and metadata/review records; retain current in-memory MVP route as demo compatibility.
- Extend CI and documentation; run migration reconciliation plus unit/integration tests.

## Deployment approval gate

Before any staging or production deployment, present and obtain approval for all of the following:

- selected database, identity, object-storage, frontend, backend, monitoring, and email/alert providers;
- the provider account/organisation that will own each resource, expected monthly cost and free-tier limits;
- domains and DNS changes, if any;
- the complete environment-variable *names* and which system supplies each value (never the values themselves);
- backup retention, recovery objective, data location, pilot-data/privacy implications, and rollback plan.
