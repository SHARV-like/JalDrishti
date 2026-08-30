"""Add provider-neutral monitoring jobs, imagery, indicators, weather, and alerts."""

from alembic import op
from app.production.database import Base
from app.production import models  # noqa: F401

revision = "0003_monitoring"
down_revision = "0002_field_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    names = ("monitoring_jobs", "imagery_acquisitions", "indicator_observations", "environmental_observations", "monitoring_alerts")
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in names])


def downgrade() -> None:
    bind = op.get_bind()
    for name in ("monitoring_alerts", "environmental_observations", "indicator_observations", "imagery_acquisitions", "monitoring_jobs"):
        Base.metadata.tables[name].drop(bind=bind)
