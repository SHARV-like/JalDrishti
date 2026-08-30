"""Add versioned recommendation rules and scenario runs."""
from alembic import op
from app.production.database import Base
from app.production import models  # noqa: F401

revision = "0004_planning"
down_revision = "0003_monitoring"
branch_labels = None
depends_on = None

def upgrade() -> None:
    names = ("recommendation_rulesets", "recommendation_runs")
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in names])

def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["recommendation_runs"].drop(bind=bind)
    Base.metadata.tables["recommendation_rulesets"].drop(bind=bind)
