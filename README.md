# JalDrishti AI MVP

JalDrishti connects field evidence, watershed geometry, prepared satellite indicators, and explainable intervention recommendations for one transparent demonstration watershed.

## Repository layout

- `frontend/` — React, Vite, and Tailwind dashboard.
- `backend/` — FastAPI service with versioned API routes and pure scoring services.
- `data/geo/` — small, illustrative GeoJSON demo layers.
- `data/images/` — clearly labelled, illustrative demo field-evidence assets.
- `data/satellite/` — prepared illustrative pilot assets and metadata.
- `docs/` — scoring assumptions and the presentation script.

All committed sample data is explicitly labelled `demo`. Do not add API keys, personal field-worker information, unapproved photos, or raw rasters to the repository.

## Prerequisites

- Node.js 20 or newer and npm 10 or newer.
- Python 3.11 or newer.

## Run locally

1. Start the API in one terminal:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

2. Start the dashboard in another terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

3. Open the URL printed by Vite (normally `http://localhost:5173`). The dashboard requests `http://localhost:8000/api/v1/watersheds`.

## Checks

```powershell
cd backend
python -m compileall app tests
python -m pytest

cd ..\frontend
npm install
npm run build
```

In Git Bash, use the equivalent commands below:

```bash
cd backend
./.venv/Scripts/python.exe -m compileall -q app tests
./.venv/Scripts/python.exe -m pytest

cd ../frontend
npm run build
```

## Continuous integration

GitHub Actions runs on every push and pull request targeting `main`. The frontend job installs dependencies with the npm cache, runs `npm run lint` only when a lint script is configured, builds the production dashboard, and checks high-severity production dependency advisories. The backend job uses the pip cache, installs `backend/requirements.txt`, compiles Python sources, runs pytest when tests are present, and checks Python dependencies for known vulnerabilities. No deployment is performed.

Open the repository's **Actions** tab in GitHub, then select **JalDrishti CI** to view a run, its job logs, and any failing step.

## Environment variables

The MVP runs with its committed demo files and requires no environment variables. When a database or storage service is introduced, create a local `.env` from a documented template; never commit real values. Any future Supabase integration must keep secret/service keys on the server only and enforce row-level security before exposing tables.

## Phase 1 production foundation

The current MVP continues to run offline with its curated demo data. Phase 1 adds an organisation-scoped production data foundation alongside it: Alembic migrations, role-aware API routes, intervention lifecycle history, audit events, and evidence upload intents. Uploaded production image bytes are designed to live in private object storage; only the object reference and review metadata belong in the database.

For a local database verification, use the bundled SQLite fallback (stored in ignored `backend/tmp/`):

```powershell
cd backend
Copy-Item ..\.env.example .env
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m app.production.cli
```

For a local PostGIS service, set a password only in your current shell, then start the supplied development container and set the matching untracked `DATABASE_URL` in `backend/.env`:

```powershell
$env:POSTGRES_PASSWORD = "choose-a-local-password"
docker compose -f docker-compose.production-foundation.yml up -d
```

Production requires PostgreSQL/PostGIS, `AUTH_MODE=oidc`, a valid issuer/audience, and private object storage. The API rejects development-header authentication when `APP_ENV=production`.
