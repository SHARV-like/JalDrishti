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

## Continuous integration

GitHub Actions runs on every push and pull request targeting `main`. The frontend job installs dependencies with the npm cache, runs `npm run lint` only when a lint script is configured, and builds the production dashboard. The backend job uses the pip cache, installs `backend/requirements.txt`, compiles Python sources, and runs pytest when tests are present. No deployment is performed.

Open the repository's **Actions** tab in GitHub, then select **JalDrishti CI** to view a run, its job logs, and any failing step.

## Environment variables

The MVP runs with its committed demo files and requires no environment variables. When a database or storage service is introduced, create a local `.env` from a documented template; never commit real values. Any future Supabase integration must keep secret/service keys on the server only and enforce row-level security before exposing tables.
