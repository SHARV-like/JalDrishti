# Phase 3: automated satellite and environmental monitoring

## Architecture

`app.services.monitoring` defines provider contracts for imagery and weather. `PreparedPilotAdapter` is the only enabled adapter: it reads the committed before/after illustrative assets without internet access. `DisabledRemoteAdapter` is the extension point for Sentinel-2, Landsat, and weather providers; it raises an explicit disabled message until provider access, cost, credentials, and scheduling are approved.

`monitoring_jobs` is the durable queue record. It uses an organisation-scoped idempotency key, attempt count, completion state, and error message. A production worker should call `run_prepared_imagery_job` (or a provider-specific replacement); API requests only queue a job, while the manual run route exists for controlled pilot/recovery runs.

## Data and alerts

Migration `0003_monitoring` adds imagery acquisitions, NDVI/NDWI observations, weather observation storage, job records, and monitoring alerts. Acquisitions retain source, acquisition time, cloud percentage, AOI coverage, processing status, quality flags, asset key, attribution, and pilot/operational status.

The pilot worker creates alerts for usable imagery and substantial positive/negative NDVI change. It is designed to add prolonged-no-imagery and review-needed alerts once scheduled live catalogues and review assignments are enabled.

## API

- `POST /api/v1/monitoring/watersheds/{id}/prepared-ingest` — Admin/Supervisor queues an idempotent pilot ingestion job.
- `POST /api/v1/monitoring/jobs/{id}/run` — Admin/Supervisor runs a queued pilot job manually.
- `GET /api/v1/monitoring/watersheds/{id}/imagery` — imagery catalogue/history.
- `GET /api/v1/monitoring/watersheds/{id}/indicators` — NDVI/NDWI time series, source, confidence, summary, and limitations.
- `GET /api/v1/monitoring/alerts` — Admin/Supervisor/Auditor open alerts.

Every indicator response and the existing dashboard satellite panel label results as observed/prepared indicators, not proof that an intervention caused a change. The limitations cover seasonal conditions, rainfall, cloud cover, and crop cycles.

## Provider activation gate

No external provider is enabled by this phase. Before enabling Sentinel-2, Landsat, rainfall/weather access, object storage, or scheduled workers, provide the provider, applicable cost/free-tier and quota, account/data-access requirements, job frequency, and environment-variable names for explicit approval.
