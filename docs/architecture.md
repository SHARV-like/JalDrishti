# JalDrishti AI production architecture

## Scope and preservation boundary

This architecture evolves the working SIH MVP without replacing its offline behaviour. The existing React dashboard, FastAPI demo routes, curated GeoJSON, prepared satellite assets, GeoProof explanations, recommendations, and PDF export remain an explicit **demo compatibility mode**. Production modules are introduced alongside them and move each screen to the new API only after parity tests pass.

No current database, provider account, storage bucket, or production credential is assumed to exist.

## System context

```text
Field worker web/PWA ─┐                    ┌─> Private object storage (images/reports)
Operations dashboard ─┼─ HTTPS/OIDC ─> FastAPI API ─> PostgreSQL + PostGIS
Auditor/report user ──┘                       │             │
                                                │             └─> Alembic migrations + RLS
                                                ├─> Job queue/worker ─> satellite/weather adapters
                                                └─> Audit, metrics, traces, error reporting

Offline demo dashboard ─> local FastAPI + curated files (no external dependency)
```

The React application is a static frontend. FastAPI owns authorisation, domain validation, persistence, signed upload/report URLs, and integration with workers. Object storage holds bytes; PostgreSQL holds only metadata and object keys.

## Components and responsibilities

| Component | Responsibility | Phase |
| --- | --- | --- |
| React/Vite application | Role-aware views, map/layers, field drafts, sync feedback, reports, accessible light/dark UI | 1–5 |
| FastAPI API | OIDC JWT verification, RBAC, organisation scoping, OpenAPI, input validation, idempotency, rate limits | 1 onward |
| PostgreSQL 16 + PostGIS | Transactional operational data, native spatial indexes/queries, RLS defence-in-depth | 1 onward |
| Private object storage | Evidence images and generated reports, encryption, retention lifecycle, short-lived signed URLs | 1 onward |
| Worker/queue | Slow or retryable jobs: metadata extraction, duplicate candidates, PDF generation, imagery ingestion, alerts | 2 onward |
| Provider adapters | Sentinel/Landsat and weather/rainfall catalogue, quality checks, manual-prepared fallback | 3 onward |
| Observability | Structured logs, traces, metrics, error reporting, audit events, health/readiness checks | 1 onward |

## Identity, tenancy, and permissions

Authentication is delegated to an OIDC provider such as Supabase Auth. FastAPI validates token signature through the issuer JWKS, issuer, audience, expiry, and the configured organisation claim; it never accepts unverified tokens. The application stores its own organisation membership as the source of authorisation.

| Role | Permitted responsibilities |
| --- | --- |
| Admin | Manage organisation membership/policies, all operational records, reviews, and exports. |
| Field Worker | Create assigned drafts, interventions, and evidence; submit but cannot independently verify. |
| Supervisor | Assign and review work, manage lifecycle, mark Verified or Needs Review. |
| Auditor | Read evidence history, decisions, exports, and audit records; no mutation. |
| Viewer | Read only, subject to geography/privacy scope. |

Every tenant-owned table includes `organisation_id`. API queries require this scope, and PostgreSQL row-level security is enabled before a live tenant is onboarded. The API must set a transaction-local organisation context after authentication; direct database access is limited to migration and administrative identities.

## Data and spatial model

The current Phase 1 foundation provides `organisations`, `users`, `memberships`, `watersheds`, `interventions`, `intervention_events`, `evidence_items`, and `audit_events`.

Future migrations add villages, risk zones, assignments/drafts, EXIF/GPS observations, review records, GeoProof runs/factors, imagery acquisitions/observations, rainfall observations, alerts, recommendation rules/runs, report/export jobs, consent, retention, and deletion-request records.

Source geometry is stored as validated GeoJSON for API interchange and as indexed PostGIS `geometry(Geometry, 4326)` for spatial filtering. Metre-distance operations use PostGIS `geography` casts or an appropriate projected coordinate system. Each imported or derived item records source, observed/acquired time, processing version, confidence/quality, attribution, and `data_status` (`demo`, `pilot`, or `operational`).

## Key flows

### Evidence submission and review

1. A field worker creates a local draft with GPS, timestamp, and consent state.
2. On sync, the API validates user, role, organisation, intervention assignment, MIME type, byte limit, and idempotency key.
3. The API creates a pending metadata record and a short-lived, scoped upload URL for private object storage.
4. The client uploads directly; a completion endpoint verifies the object metadata/checksum before it can be submitted.
5. A worker extracts EXIF and creates GeoProof, duplicate-candidate, and metadata-consistency observations.
6. A supervisor reviews evidence; every action appends immutable history and an audit event.

These checks identify inconsistencies for review; none is described as fraud-proof verification.

### Geospatial and monitoring flow

1. Versioned watershed/risk/intervention layers enter via validated import jobs.
2. PostGIS performs boundary, search, filtering, and proximity queries.
3. Scheduled adapters record imagery/weather acquisition attempts, provider/source, cloud/quality state, and fallback reason.
4. Analysis jobs persist observed NDVI/NDWI and change results with dates, sources, method, confidence, and limitations.
5. The UI shows observed indicators, never causal impact claims, and retains prepared/manual imagery when a provider is unavailable.

### Reporting flow

Report requests create jobs that read only authorised, consent-filtered records. A worker writes the rendered PDF/XLSX to private object storage, records provenance and expiry, then provides a short-lived download URL. Exports and downloads are audit events.

## Security and operational controls

- Strict Pydantic schemas, pagination/filter allow-lists, bounded upload sizes, MIME plus file-signature inspection, checksum tracking, malware-scanning integration point, and content-disposition headers.
- Per-organisation rate limits for upload intent, login-adjacent routes, costly spatial operations, exports, and provider jobs. Return structured `429` responses with retry guidance.
- RFC 7807-style error responses with request IDs; do not expose stack traces, keys, object paths, tokens, or GPS details to unauthorised users.
- Development/staging/production settings are separate. Production refuses development-header authentication, non-TLS origin settings, local object storage, and SQLite fallback.
- Secrets are held only in the selected provider's secret manager. `.env.example` documents names only; it contains no credentials.
- Audit events are append-only application records; database permissions prevent ordinary application roles from altering them.
- Backups use encrypted point-in-time recovery, tested restoration, documented RPO/RTO, retention lifecycle, consent minimisation, and deletion/export procedures.

## Environments and deployment topology

| Environment | Purpose | Data | Provider state |
| --- | --- | --- | --- |
| Development | Fast local iteration | Curated demo fixtures / disposable local DB | No cloud account required |
| Staging | Migration, integration, and release validation | Synthetic or approved non-personal pilot copy | Isolated project, bucket, auth tenant, and database |
| Production | Field operations | Approved operational data only | Separate account/project, least privilege, backups, monitoring |

The deployment target remains deliberately undecided. A likely topology is static React hosting, a containerised FastAPI service, managed PostgreSQL/PostGIS, S3-compatible private object storage, and managed OIDC. Provider choice, cost, domains, accounts, and variables are a mandatory approval gate before provisioning.

## Migration, rollback, and compatibility

1. Freeze and checksum curated demo fixtures.
2. Apply an additive Alembic migration to an empty database.
3. Run the idempotent seed importer and reconcile source ID, count, geometry validity, attribution, and map output.
4. Serve the existing demo UI through its compatibility routes while read parity is measured.
5. Migrate one read surface at a time behind a feature flag; leave demo fallback available.
6. For a failed release, disable the feature flag and return that surface to compatibility mode; never use destructive migration rollback against production data without a tested recovery runbook.

## Phase gates

Phase 1 is the foundation already present in the repository and documented here. Phase 2 adds evidence workflow, review history, stronger GeoProof, and offline sync. Phase 3 adds monitoring adapters and observed indicators. Phase 4 adds versioned recommendation rules and then scenarios. Phase 5 adds operations dashboards, exports, governance, and recovery exercises. Every phase ends with tests, migration verification, security review, changed-file summary, and user approval before commit/push.
