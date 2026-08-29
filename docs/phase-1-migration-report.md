# Phase 1 migration verification report

## Scope

This report verifies the safe import of JalDrishti's curated MVP GeoJSON into the new organisation-scoped Phase 1 schema. It is a demo-data migration only; no personal data, raw imagery, or production credentials are included.

## Verification result

The initial migration applied revision `0001_production_foundation` to a fresh local SQLite verification database. It created the organisation, membership, watershed, intervention, lifecycle-event, evidence, and audit tables. The PostGIS extension is enabled automatically when this same migration runs against PostgreSQL.

The seed import then produced:

| Item | Result |
| --- | ---: |
| Organisations | 1 (`jaldirshti-demo`) |
| Demo watersheds | 1 |
| Demo interventions | 5 |
| Duplicate records after a second seed run | 0 |

## Controls verified

- Every migrated watershed and intervention is labelled `data_status: demo`.
- Source geometries remain GeoJSON for portable import/export; PostgreSQL targets have PostGIS enabled for subsequent indexed spatial fields and queries.
- External IDs are unique per organisation, making repeated seed runs safe.
- The bootstrap administrator has an explicit organisation membership and role.
- The seed process writes an audit event only when it creates records.

## Operational handover

Run `alembic upgrade head` before the seed/import step in each environment. The production deployment must use PostgreSQL/PostGIS, OIDC authentication, a private object-storage adapter, and a secret manager. The SQLite fallback exists solely for local tests and offline demo development.
