# Database migrations

Phase 1 uses Alembic migrations against PostgreSQL 16 with PostGIS in deployed environments. During local MVP compatibility tests, SQLite may be used only for relational permission and seed checks; it is not a substitute for PostGIS spatial validation.

Before production deployment, generate/review the initial migration from `app.production.models`, enable the PostGIS extension, and apply it through a controlled release job. The seed command is idempotent:

```bash
python -m app.production.cli
```

It imports only the committed, labelled demo GeoJSON into a dedicated demo organisation.
