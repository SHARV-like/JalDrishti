from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.production.audit import record_audit
from app.production.auth import Principal, require_roles
from app.production.database import get_session
from app.production.models import EvidenceItem, Intervention, InterventionEvent, LifecycleStatus, Role, Watershed
from app.production.storage import create_upload_intent

router = APIRouter(tags=["production foundation"])

TRANSITIONS: dict[str, set[str]] = {
    LifecycleStatus.PLANNED.value: {LifecycleStatus.IN_PROGRESS.value},
    LifecycleStatus.IN_PROGRESS.value: {LifecycleStatus.COMPLETED.value},
    LifecycleStatus.COMPLETED.value: {LifecycleStatus.SUBMITTED.value},
    LifecycleStatus.SUBMITTED.value: {LifecycleStatus.VERIFIED.value, LifecycleStatus.NEEDS_REVIEW.value},
    LifecycleStatus.NEEDS_REVIEW.value: {LifecycleStatus.SUBMITTED.value},
    LifecycleStatus.VERIFIED.value: set(),
}


class InterventionCreate(BaseModel):
    watershed_id: str
    external_id: str = Field(min_length=3, max_length=160)
    name: str = Field(min_length=3, max_length=200)
    intervention_type: str = Field(min_length=3, max_length=80)
    geometry: dict


class LifecycleTransition(BaseModel):
    to_status: Literal["planned", "in_progress", "completed", "submitted", "verified", "needs_review"]
    reason: str = Field(min_length=3, max_length=2000)


class EvidenceIntentRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: Literal["image/jpeg", "image/png"]
    size_bytes: int = Field(gt=0)


@router.get("/me")
def get_me(principal: Principal = Depends(require_roles(Role.ADMIN, Role.FIELD_WORKER, Role.SUPERVISOR, Role.AUDITOR, Role.VIEWER))) -> dict:
    return {"user_id": principal.user_id, "organisation_id": principal.organisation_id, "role": principal.role.value}


@router.get("/production/interventions")
def list_interventions(session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.FIELD_WORKER, Role.SUPERVISOR, Role.AUDITOR, Role.VIEWER))) -> list[dict]:
    rows = session.scalars(select(Intervention).where(Intervention.organisation_id == principal.organisation_id).order_by(Intervention.name)).all()
    return [{"id": item.id, "external_id": item.external_id, "name": item.name, "type": item.intervention_type, "status": item.lifecycle_status, "watershed_id": item.watershed_id, "geometry": item.geometry, "data_status": item.data_status} for item in rows]


@router.post("/production/interventions", status_code=status.HTTP_201_CREATED)
def create_intervention(payload: InterventionCreate, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.FIELD_WORKER, Role.SUPERVISOR))) -> dict:
    watershed = session.get(Watershed, payload.watershed_id)
    if not watershed or watershed.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watershed not found in this organisation")
    if session.scalar(select(Intervention).where(Intervention.organisation_id == principal.organisation_id, Intervention.external_id == payload.external_id)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An intervention with this source ID already exists")
    item = Intervention(organisation_id=principal.organisation_id, watershed_id=watershed.id, external_id=payload.external_id, name=payload.name, intervention_type=payload.intervention_type, lifecycle_status=LifecycleStatus.PLANNED.value, geometry=payload.geometry, data_status="field")
    session.add(item); session.flush()
    session.add(InterventionEvent(organisation_id=principal.organisation_id, intervention_id=item.id, from_status=None, to_status=LifecycleStatus.PLANNED.value, reason="Intervention created", actor_id=principal.user_id))
    record_audit(session, principal.organisation_id, principal.user_id, "intervention_created", "intervention", item.id)
    return {"id": item.id, "status": item.lifecycle_status}


@router.post("/production/interventions/{intervention_id}/transition")
def transition_intervention(intervention_id: str, payload: LifecycleTransition, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.FIELD_WORKER, Role.SUPERVISOR))) -> dict:
    item = session.get(Intervention, intervention_id)
    if not item or item.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found")
    if payload.to_status in {LifecycleStatus.VERIFIED.value, LifecycleStatus.NEEDS_REVIEW.value} and principal.role not in {Role.ADMIN, Role.SUPERVISOR}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin or Supervisor can review an intervention")
    if payload.to_status not in TRANSITIONS[item.lifecycle_status]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invalid lifecycle transition from {item.lifecycle_status} to {payload.to_status}")
    previous = item.lifecycle_status; item.lifecycle_status = payload.to_status
    session.add(InterventionEvent(organisation_id=principal.organisation_id, intervention_id=item.id, from_status=previous, to_status=item.lifecycle_status, reason=payload.reason, actor_id=principal.user_id))
    record_audit(session, principal.organisation_id, principal.user_id, "intervention_transitioned", "intervention", item.id, {"from": previous, "to": item.lifecycle_status})
    return {"id": item.id, "from_status": previous, "to_status": item.lifecycle_status}


@router.post("/production/interventions/{intervention_id}/evidence-intents", status_code=status.HTTP_201_CREATED)
def create_evidence_intent(intervention_id: str, payload: EvidenceIntentRequest, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.FIELD_WORKER, Role.SUPERVISOR))) -> dict:
    intervention = session.get(Intervention, intervention_id)
    if not intervention or intervention.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found")
    provisional = EvidenceItem(organisation_id=principal.organisation_id, intervention_id=intervention.id, object_key="pending", filename=payload.filename, content_type=payload.content_type, size_bytes=payload.size_bytes, review_status="draft", created_by=principal.user_id)
    session.add(provisional); session.flush()
    try:
        intent = create_upload_intent(principal.organisation_id, provisional.id, payload.content_type, payload.size_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    provisional.object_key = intent.object_key
    record_audit(session, principal.organisation_id, principal.user_id, "evidence_upload_intent_created", "evidence", provisional.id, {"content_type": payload.content_type, "size_bytes": payload.size_bytes})
    return {"evidence_id": provisional.id, "object_key": intent.object_key, "upload_url": intent.upload_url, "expires_in_seconds": intent.expires_in_seconds, "next_step": "Upload directly to configured private object storage, then complete the evidence record."}
