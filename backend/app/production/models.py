import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.production.database import Base


def uuid_id() -> str:
    return str(uuid.uuid4())


class Role(StrEnum):
    ADMIN = "admin"
    FIELD_WORKER = "field_worker"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class LifecycleStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"


class Organisation(Base):
    __tablename__ = "organisations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organisation_id", "user_id", name="uq_membership_organisation_user"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(30), default=Role.VIEWER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Watershed(Base):
    __tablename__ = "watersheds"
    __table_args__ = (UniqueConstraint("organisation_id", "external_id", name="uq_watershed_org_external"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(160))
    name: Mapped[str] = mapped_column(String(200))
    geojson: Mapped[dict] = mapped_column(JSON)
    data_status: Mapped[str] = mapped_column(String(30), default="demo")
    source_attribution: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Village(Base):
    __tablename__ = "villages"
    __table_args__ = (UniqueConstraint("organisation_id", "external_id", name="uq_village_org_external"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    watershed_id: Mapped[str] = mapped_column(ForeignKey("watersheds.id", ondelete="RESTRICT"), index=True)
    external_id: Mapped[str] = mapped_column(String(160))
    name: Mapped[str] = mapped_column(String(200))
    geometry: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    data_status: Mapped[str] = mapped_column(String(30), default="pilot")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskZone(Base):
    __tablename__ = "risk_zones"
    __table_args__ = (UniqueConstraint("organisation_id", "external_id", name="uq_risk_zone_org_external"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    watershed_id: Mapped[str] = mapped_column(ForeignKey("watersheds.id", ondelete="RESTRICT"), index=True)
    external_id: Mapped[str] = mapped_column(String(160))
    name: Mapped[str] = mapped_column(String(200))
    risk_level: Mapped[str] = mapped_column(String(30))
    geometry: Mapped[dict] = mapped_column(JSON)
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    data_status: Mapped[str] = mapped_column(String(30), default="pilot")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Intervention(Base):
    __tablename__ = "interventions"
    __table_args__ = (UniqueConstraint("organisation_id", "external_id", name="uq_intervention_org_external"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    watershed_id: Mapped[str] = mapped_column(ForeignKey("watersheds.id", ondelete="RESTRICT"), index=True)
    village_id: Mapped[str | None] = mapped_column(ForeignKey("villages.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id: Mapped[str] = mapped_column(String(160))
    name: Mapped[str] = mapped_column(String(200))
    intervention_type: Mapped[str] = mapped_column(String(80))
    lifecycle_status: Mapped[str] = mapped_column(String(30), default=LifecycleStatus.PLANNED.value)
    assigned_reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    geometry: Mapped[dict] = mapped_column(JSON)
    data_status: Mapped[str] = mapped_column(String(30), default="demo")
    source_attribution: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InterventionEvent(Base):
    __tablename__ = "intervention_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    intervention_id: Mapped[str] = mapped_column(ForeignKey("interventions.id", ondelete="CASCADE"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    intervention_id: Mapped[str] = mapped_column(ForeignKey("interventions.id", ondelete="CASCADE"), index=True)
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review_status: Mapped[str] = mapped_column(String(30), default="draft")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceObservation(Base):
    __tablename__ = "evidence_observations"
    __table_args__ = (UniqueConstraint("evidence_id", name="uq_evidence_observation_evidence"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_items.id", ondelete="CASCADE"), index=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    device_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    geoproof_score: Mapped[int] = mapped_column(Integer, default=0)
    geoproof_factors: Mapped[dict] = mapped_column(JSON, default=dict)
    consistency_warnings: Mapped[list] = mapped_column(JSON, default=list)
    duplicate_warning: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VerificationReview(Base):
    __tablename__ = "verification_reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    intervention_id: Mapped[str] = mapped_column(ForeignKey("interventions.id", ondelete="CASCADE"), index=True)
    evidence_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_items.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    outcome: Mapped[str] = mapped_column(String(30), default=LifecycleStatus.NEEDS_REVIEW.value)
    comments: Mapped[str] = mapped_column(Text)
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MonitoringJob(Base):
    __tablename__ = "monitoring_jobs"
    __table_args__ = (UniqueConstraint("organisation_id", "idempotency_key", name="uq_monitoring_job_idempotency"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    watershed_id: Mapped[str] = mapped_column(ForeignKey("watersheds.id", ondelete="CASCADE"), index=True)
    intervention_id: Mapped[str | None] = mapped_column(ForeignKey("interventions.id", ondelete="SET NULL"), nullable=True, index=True)
    job_type: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImageryAcquisition(Base):
    __tablename__ = "imagery_acquisitions"
    __table_args__ = (UniqueConstraint("organisation_id", "external_id", name="uq_imagery_org_external"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    watershed_id: Mapped[str] = mapped_column(ForeignKey("watersheds.id", ondelete="CASCADE"), index=True)
    intervention_id: Mapped[str | None] = mapped_column(ForeignKey("interventions.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(80))
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    cloud_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_geojson: Mapped[dict] = mapped_column(JSON)
    processing_status: Mapped[str] = mapped_column(String(30), default="ready")
    quality_flags: Mapped[list] = mapped_column(JSON, default=list)
    asset_key: Mapped[str] = mapped_column(String(500))
    source_attribution: Mapped[dict] = mapped_column(JSON, default=dict)
    data_status: Mapped[str] = mapped_column(String(30), default="pilot")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndicatorObservation(Base):
    __tablename__ = "indicator_observations"
    __table_args__ = (UniqueConstraint("acquisition_id", name="uq_indicator_acquisition"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    acquisition_id: Mapped[str] = mapped_column(ForeignKey("imagery_acquisitions.id", ondelete="CASCADE"), index=True)
    ndvi: Mapped[float | None] = mapped_column(Float, nullable=True)
    ndwi: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_summary: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(30), default="pilot")
    limitations: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EnvironmentalObservation(Base):
    __tablename__ = "environmental_observations"
    __table_args__ = (UniqueConstraint("organisation_id", "external_id", name="uq_environment_org_external"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    watershed_id: Mapped[str] = mapped_column(ForeignKey("watersheds.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str] = mapped_column(String(80))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    quality_flags: Mapped[list] = mapped_column(JSON, default=list)
    data_status: Mapped[str] = mapped_column(String(30), default="pilot")


class MonitoringAlert(Base):
    __tablename__ = "monitoring_alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    watershed_id: Mapped[str] = mapped_column(ForeignKey("watersheds.id", ondelete="CASCADE"), index=True)
    intervention_id: Mapped[str | None] = mapped_column(ForeignKey("interventions.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(30), default="info")
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecommendationRuleset(Base):
    __tablename__ = "recommendation_rulesets"
    __table_args__ = (UniqueConstraint("organisation_id", "region_key", "version", name="uq_ruleset_org_region_version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    region_key: Mapped[str] = mapped_column(String(120), default="default")
    version: Mapped[str] = mapped_column(String(80))
    rules: Mapped[dict] = mapped_column(JSON)
    assumptions: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    watershed_id: Mapped[str] = mapped_column(ForeignKey("watersheds.id", ondelete="CASCADE"), index=True)
    risk_zone_id: Mapped[str] = mapped_column(ForeignKey("risk_zones.id", ondelete="CASCADE"), index=True)
    ruleset_id: Mapped[str] = mapped_column(ForeignKey("recommendation_rulesets.id", ondelete="RESTRICT"), index=True)
    ruleset_version: Mapped[str] = mapped_column(String(80))
    inputs: Mapped[dict] = mapped_column(JSON)
    results: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="estimate")
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_id)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(200))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
