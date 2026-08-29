"""Create the Phase 1 organisation, intervention, evidence, and audit foundation.

The application keeps GeoJSON as the portable interchange representation. On
PostgreSQL/PostGIS deployments, this revision also enables PostGIS so future
revisions can add indexed native geometry columns without a platform change.
"""

from alembic import op

from app.production.database import Base
from app.production import models  # noqa: F401 - register SQLAlchemy models


revision = "0001_production_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    # Keep this revision frozen: future ORM models must be created only by
    # their own revisions, never as a side effect of an earlier migration.
    foundation_tables = [
        Base.metadata.tables[name]
        for name in (
            "organisations", "users", "memberships", "watersheds", "interventions",
            "intervention_events", "evidence_items", "audit_events",
        )
    ]
    Base.metadata.create_all(bind=bind, tables=foundation_tables)
    if bind.dialect.name == "postgresql":
        # GeoJSON remains the portable API/import representation. These native
        # columns give production queries spatial indexes and metre-safe
        # calculations (via geography casts) without changing the MVP payloads.
        op.execute("ALTER TABLE watersheds ADD COLUMN geom geometry(Geometry, 4326)")
        op.execute("ALTER TABLE interventions ADD COLUMN geom geometry(Geometry, 4326)")
        op.execute("CREATE INDEX ix_watersheds_geom ON watersheds USING GIST (geom)")
        op.execute("CREATE INDEX ix_interventions_geom ON interventions USING GIST (geom)")


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
