"""Add Phase 2 field-operations, evidence-observation, and review records."""

from alembic import op
import sqlalchemy as sa


revision = "0002_field_operations"
down_revision = "0001_production_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "villages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organisation_id", sa.String(36), sa.ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("watershed_id", sa.String(36), sa.ForeignKey("watersheds.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("external_id", sa.String(160), nullable=False), sa.Column("name", sa.String(200), nullable=False),
        sa.Column("geometry", sa.JSON(), nullable=True), sa.Column("data_status", sa.String(30), nullable=False, server_default="pilot"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("organisation_id", "external_id", name="uq_village_org_external"),
    )
    op.create_table(
        "risk_zones",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("organisation_id", sa.String(36), sa.ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("watershed_id", sa.String(36), sa.ForeignKey("watersheds.id", ondelete="RESTRICT"), nullable=False), sa.Column("external_id", sa.String(160), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), sa.Column("risk_level", sa.String(30), nullable=False), sa.Column("geometry", sa.JSON(), nullable=False), sa.Column("conditions", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("data_status", sa.String(30), nullable=False, server_default="pilot"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("organisation_id", "external_id", name="uq_risk_zone_org_external"),
    )
    bind = op.get_bind()
    existing_columns = {column["name"] for column in sa.inspect(bind).get_columns("interventions")}
    if "village_id" not in existing_columns:
        op.add_column("interventions", sa.Column("village_id", sa.String(36), nullable=True))
    if "assigned_reviewer_id" not in existing_columns:
        op.add_column("interventions", sa.Column("assigned_reviewer_id", sa.String(200), nullable=True))
    if bind.dialect.name != "sqlite":
        existing_foreign_keys = {foreign_key.get("name") for foreign_key in sa.inspect(bind).get_foreign_keys("interventions")}
        if "fk_intervention_village" not in existing_foreign_keys:
            op.create_foreign_key("fk_intervention_village", "interventions", "villages", ["village_id"], ["id"], ondelete="SET NULL")
        if "fk_intervention_reviewer" not in existing_foreign_keys:
            op.create_foreign_key("fk_intervention_reviewer", "interventions", "users", ["assigned_reviewer_id"], ["id"], ondelete="SET NULL")
    op.create_table(
        "evidence_observations",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("organisation_id", sa.String(36), sa.ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_id", sa.String(36), sa.ForeignKey("evidence_items.id", ondelete="CASCADE"), nullable=False), sa.Column("captured_at", sa.DateTime(timezone=True)),
        sa.Column("latitude", sa.Float()), sa.Column("longitude", sa.Float()), sa.Column("gps_accuracy_m", sa.Float()), sa.Column("device_source", sa.String(200)),
        sa.Column("geoproof_score", sa.Integer(), nullable=False, server_default="0"), sa.Column("geoproof_factors", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("consistency_warnings", sa.JSON(), nullable=False, server_default="[]"), sa.Column("duplicate_warning", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("evidence_id", name="uq_evidence_observation_evidence"),
    )
    op.create_table(
        "verification_reviews",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("organisation_id", sa.String(36), sa.ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intervention_id", sa.String(36), sa.ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False), sa.Column("evidence_id", sa.String(36), sa.ForeignKey("evidence_items.id", ondelete="SET NULL")),
        sa.Column("assigned_to", sa.String(200), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("outcome", sa.String(30), nullable=False, server_default="needs_review"),
        sa.Column("comments", sa.Text(), nullable=False), sa.Column("reviewed_by", sa.String(200), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("verification_reviews")
    op.drop_table("evidence_observations")
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint("fk_intervention_reviewer", "interventions", type_="foreignkey")
        op.drop_constraint("fk_intervention_village", "interventions", type_="foreignkey")
    op.drop_column("interventions", "assigned_reviewer_id")
    op.drop_column("interventions", "village_id")
    op.drop_table("risk_zones")
    op.drop_table("villages")
