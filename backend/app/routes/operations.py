"""Phase 2 organisation-scoped field operations and review routes.

All verification results are decision support. A low score, duplicate warning,
or metadata inconsistency creates/retains a review item; it is never a fraud
determination.
"""

from datetime import datetime, timezone
from math import asin, cos, radians, sin, sqrt
import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator, model_validator
from shapely.geometry import Point, shape
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.production.audit import record_audit
from app.production.auth import Principal, require_roles
from app.production.database import get_session
from app.production.models import (
    EvidenceItem, EvidenceObservation, Intervention, InterventionEvent,
    LifecycleStatus, RiskZone, Role, VerificationReview, Village, Watershed,
)


router = APIRouter(prefix="/operations", tags=["field operations"])
SHA256 = re.compile(r"^[a-fA-F0-9]{64}$")


def _distance_m(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    earth_radius_m = 6_371_000
    delta_latitude, delta_longitude = radians(latitude_b - latitude_a), radians(longitude_b - longitude_a)
    value = sin(delta_latitude / 2) ** 2 + cos(radians(latitude_a)) * cos(radians(latitude_b)) * sin(delta_longitude / 2) ** 2
    return 2 * earth_radius_m * asin(sqrt(value))


class VillageCreate(BaseModel):
    watershed_id: str
    external_id: str = Field(min_length=3, max_length=160)
    name: str = Field(min_length=2, max_length=200)
    geometry: dict | None = None


class RiskZoneCreate(BaseModel):
    watershed_id: str
    external_id: str = Field(min_length=3, max_length=160)
    name: str = Field(min_length=2, max_length=200)
    risk_level: str = Field(pattern="^(high|moderate|low)$")
    geometry: dict
    conditions: dict = Field(default_factory=dict)


class EvidenceCompletion(BaseModel):
    capture_time: datetime | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    gps_accuracy_m: float | None = Field(default=None, ge=0, le=10_000)
    device_source: str | None = Field(default=None, max_length=200)
    image_sha256: str | None = None

    @field_validator("image_sha256")
    @classmethod
    def validate_hash(cls, value: str | None) -> str | None:
        if value and not SHA256.fullmatch(value):
            raise ValueError("image_sha256 must be a SHA-256 hexadecimal digest")
        return value.lower() if value else None

    @model_validator(mode="after")
    def validate_coordinate_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class SubmitForReview(BaseModel):
    comments: str = Field(min_length=3, max_length=2000)
    assigned_to: str | None = Field(default=None, max_length=200)


class ReviewDecision(BaseModel):
    outcome: str = Field(pattern="^(approved|rejected|needs_review)$")
    comments: str = Field(min_length=3, max_length=4000)


def _org_watershed(session: Session, principal: Principal, watershed_id: str) -> Watershed:
    watershed = session.get(Watershed, watershed_id)
    if not watershed or watershed.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=404, detail="Watershed not found in this organisation")
    return watershed


def _org_intervention(session: Session, principal: Principal, intervention_id: str) -> Intervention:
    item = session.get(Intervention, intervention_id)
    if not item or item.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=404, detail="Intervention not found in this organisation")
    return item


def _geoproof(session: Session, intervention: Intervention, payload: EvidenceCompletion) -> tuple[int, dict, list[str]]:
    warnings: list[str] = []
    factors: dict[str, dict] = {}
    if payload.latitude is None or payload.longitude is None:
        factors["gps_available"] = {"points": 0, "message": "No complete GPS coordinate pair was supplied."}
        factors["boundary"] = {"points": 0, "message": "Boundary check could not run without GPS."}
        factors["distance"] = {"points": 0, "message": "Distance check could not run without GPS."}
        factors["capture_time"] = {"points": 10 if payload.capture_time else 0, "message": "Capture time is available." if payload.capture_time else "No capture time was supplied."}
        return factors["capture_time"]["points"], factors, ["GPS metadata missing; manual review required."]

    watershed = session.get(Watershed, intervention.watershed_id)
    point = Point(payload.longitude, payload.latitude)
    inside = bool(watershed and shape(watershed.geojson).covers(point))
    candidates = session.scalars(select(Intervention).where(Intervention.organisation_id == intervention.organisation_id)).all()
    distances = []
    for candidate in candidates:
        coordinates = candidate.geometry.get("coordinates", [])
        if len(coordinates) >= 2:
            distances.append((_distance_m(payload.latitude, payload.longitude, coordinates[1], coordinates[0]), candidate))
    nearest_m, nearest = min(distances, default=(None, None), key=lambda row: row[0] if row[0] is not None else float("inf"))
    accurate = payload.gps_accuracy_m is None or payload.gps_accuracy_m <= 50
    if not accurate:
        warnings.append("GPS accuracy is above the 50 m review threshold.")
    if not inside:
        warnings.append("GPS point lies outside the watershed boundary.")
    factors = {
        "gps_available": {"points": 20, "message": "A valid latitude/longitude pair is available."},
        "gps_accuracy": {"points": 0 if not accurate else 5, "message": "GPS accuracy is within 50 m." if accurate else "GPS accuracy exceeds 50 m; no accuracy points awarded."},
        "boundary": {"points": 45 if inside else 0, "message": "Location is inside the watershed boundary." if inside else "Location is outside the watershed boundary."},
        "distance": {"points": 20 if nearest_m is not None and nearest_m <= 150 else 0, "message": f"Nearest registered intervention is {nearest_m:.1f} m away." if nearest_m is not None else "No registered intervention geometry is available."},
        "capture_time": {"points": 10 if payload.capture_time else 0, "message": "Capture time is available." if payload.capture_time else "No capture time was supplied."},
    }
    if nearest:
        factors["distance"]["nearest_intervention_id"] = nearest.id
    return sum(item["points"] for item in factors.values()), factors, warnings


@router.post("/villages", status_code=status.HTTP_201_CREATED)
def create_village(payload: VillageCreate, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN))) -> dict:
    _org_watershed(session, principal, payload.watershed_id)
    if session.scalar(select(Village).where(Village.organisation_id == principal.organisation_id, Village.external_id == payload.external_id)):
        raise HTTPException(status_code=409, detail="Village source ID already exists")
    village = Village(organisation_id=principal.organisation_id, **payload.model_dump())
    session.add(village); session.flush()
    record_audit(session, principal.organisation_id, principal.user_id, "village_created", "village", village.id)
    return {"id": village.id, "name": village.name}


@router.post("/risk-zones", status_code=status.HTTP_201_CREATED)
def create_risk_zone(payload: RiskZoneCreate, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN))) -> dict:
    _org_watershed(session, principal, payload.watershed_id)
    if session.scalar(select(RiskZone).where(RiskZone.organisation_id == principal.organisation_id, RiskZone.external_id == payload.external_id)):
        raise HTTPException(status_code=409, detail="Risk-zone source ID already exists")
    zone = RiskZone(organisation_id=principal.organisation_id, **payload.model_dump())
    session.add(zone); session.flush()
    record_audit(session, principal.organisation_id, principal.user_id, "risk_zone_created", "risk_zone", zone.id)
    return {"id": zone.id, "risk_level": zone.risk_level}


@router.post("/evidence/{evidence_id}/complete")
def complete_evidence(evidence_id: str, payload: EvidenceCompletion, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.FIELD_WORKER, Role.SUPERVISOR))) -> dict:
    evidence = session.get(EvidenceItem, evidence_id)
    if not evidence or evidence.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=404, detail="Evidence not found in this organisation")
    if evidence.created_by != principal.user_id and principal.role == Role.FIELD_WORKER:
        raise HTTPException(status_code=403, detail="Field Workers can only complete their own evidence")
    intervention = _org_intervention(session, principal, evidence.intervention_id)
    score, factors, warnings = _geoproof(session, intervention, payload)
    duplicate = bool(payload.image_sha256 and session.scalar(select(EvidenceItem).where(EvidenceItem.organisation_id == principal.organisation_id, EvidenceItem.sha256 == payload.image_sha256, EvidenceItem.id != evidence.id)))
    if duplicate:
        warnings.append("A matching image hash exists in this organisation; manual duplicate review required.")
    evidence.sha256 = payload.image_sha256
    evidence.review_status = LifecycleStatus.NEEDS_REVIEW.value if warnings or score < 80 else "ready_for_review"
    observation = session.scalar(select(EvidenceObservation).where(EvidenceObservation.evidence_id == evidence.id))
    if observation:
        observation.captured_at = payload.capture_time
        observation.latitude = payload.latitude
        observation.longitude = payload.longitude
        observation.gps_accuracy_m = payload.gps_accuracy_m
        observation.device_source = payload.device_source
        observation.geoproof_score = score
        observation.geoproof_factors = factors
        observation.consistency_warnings = warnings
        observation.duplicate_warning = duplicate
    else:
        observation = EvidenceObservation(organisation_id=principal.organisation_id, evidence_id=evidence.id, captured_at=payload.capture_time, latitude=payload.latitude, longitude=payload.longitude, gps_accuracy_m=payload.gps_accuracy_m, device_source=payload.device_source, geoproof_score=score, geoproof_factors=factors, consistency_warnings=warnings, duplicate_warning=duplicate)
        session.add(observation)
    record_audit(session, principal.organisation_id, principal.user_id, "evidence_completed", "evidence", evidence.id, {"geoproof_score": score, "warnings": warnings})
    return {"evidence_id": evidence.id, "review_status": evidence.review_status, "geoproof_score": score, "factors": factors, "warnings": warnings, "decision_support_note": "GeoProof is decision support, not fraud-proof verification."}


@router.post("/interventions/{intervention_id}/submit")
def submit_for_review(intervention_id: str, payload: SubmitForReview, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.FIELD_WORKER, Role.SUPERVISOR))) -> dict:
    item = _org_intervention(session, principal, intervention_id)
    if item.lifecycle_status not in {LifecycleStatus.COMPLETED.value, LifecycleStatus.NEEDS_REVIEW.value}:
        raise HTTPException(status_code=409, detail="Only Completed or Needs Review interventions can be submitted")
    if payload.assigned_to:
        item.assigned_reviewer_id = payload.assigned_to
    previous = item.lifecycle_status; item.lifecycle_status = LifecycleStatus.SUBMITTED.value
    review = VerificationReview(organisation_id=principal.organisation_id, intervention_id=item.id, assigned_to=item.assigned_reviewer_id, comments=payload.comments)
    session.add_all([review, InterventionEvent(organisation_id=principal.organisation_id, intervention_id=item.id, from_status=previous, to_status=item.lifecycle_status, reason=payload.comments, actor_id=principal.user_id)])
    session.flush()
    record_audit(session, principal.organisation_id, principal.user_id, "intervention_submitted", "intervention", item.id)
    return {"id": item.id, "status": item.lifecycle_status, "review_id": review.id}


@router.get("/reviews/queue")
def review_queue(session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.SUPERVISOR, Role.AUDITOR))) -> list[dict]:
    query = select(VerificationReview).where(VerificationReview.organisation_id == principal.organisation_id, VerificationReview.outcome == LifecycleStatus.NEEDS_REVIEW.value)
    if principal.role in {Role.SUPERVISOR, Role.AUDITOR}:
        query = query.where((VerificationReview.assigned_to == principal.user_id) | (VerificationReview.assigned_to.is_(None)))
    rows = session.scalars(query.order_by(VerificationReview.created_at.desc())).all()
    return [{"id": row.id, "intervention_id": row.intervention_id, "evidence_id": row.evidence_id, "assigned_to": row.assigned_to, "comments": row.comments, "outcome": row.outcome} for row in rows]


@router.post("/reviews/{review_id}")
def decide_review(review_id: str, payload: ReviewDecision, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.SUPERVISOR, Role.AUDITOR))) -> dict:
    review = session.get(VerificationReview, review_id)
    if not review or review.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=404, detail="Review not found in this organisation")
    if review.assigned_to and review.assigned_to != principal.user_id and principal.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Review is assigned to another reviewer")
    item = _org_intervention(session, principal, review.intervention_id)
    review.outcome, review.comments, review.reviewed_by, review.reviewed_at = payload.outcome, payload.comments, principal.user_id, datetime.now(timezone.utc)
    target = LifecycleStatus.VERIFIED.value if payload.outcome == "approved" else LifecycleStatus.NEEDS_REVIEW.value
    previous = item.lifecycle_status; item.lifecycle_status = target
    session.add(InterventionEvent(organisation_id=principal.organisation_id, intervention_id=item.id, from_status=previous, to_status=target, reason=payload.comments, actor_id=principal.user_id))
    record_audit(session, principal.organisation_id, principal.user_id, "review_decided", "verification_review", review.id, {"outcome": payload.outcome})
    return {"review_id": review.id, "outcome": review.outcome, "intervention_status": item.lifecycle_status}
