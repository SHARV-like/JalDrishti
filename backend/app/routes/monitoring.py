from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.production.auth import Principal, require_roles
from app.production.database import get_session
from app.production.models import EvidenceItem, ImageryAcquisition, IndicatorObservation, MonitoringAlert, MonitoringJob, Role, Watershed
from app.production.monitoring_jobs import run_prepared_imagery_job

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

class QueuePreparedIngest(BaseModel):
    intervention_id: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=200)

def watershed_for(session: Session, principal: Principal, watershed_id: str) -> Watershed:
    item = session.get(Watershed, watershed_id)
    if not item or item.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=404, detail="Watershed not found in this organisation")
    return item

@router.post("/watersheds/{watershed_id}/prepared-ingest", status_code=status.HTTP_202_ACCEPTED)
def queue_prepared_ingest(watershed_id: str, payload: QueuePreparedIngest, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.SUPERVISOR))) -> dict:
    watershed_for(session, principal, watershed_id)
    job = session.scalar(select(MonitoringJob).where(MonitoringJob.organisation_id == principal.organisation_id, MonitoringJob.idempotency_key == payload.idempotency_key))
    if not job:
        job = MonitoringJob(organisation_id=principal.organisation_id, watershed_id=watershed_id, intervention_id=payload.intervention_id, job_type="prepared_imagery_ingest", idempotency_key=payload.idempotency_key, requested_by=principal.user_id)
        session.add(job); session.flush()
    return {"job_id": job.id, "status": job.status, "next_step": "Run this queued job through the monitoring worker or the authorised manual run endpoint."}

@router.post("/jobs/{job_id}/run")
def run_job(job_id: str, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.SUPERVISOR))) -> dict:
    job = session.get(MonitoringJob, job_id)
    if not job or job.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=404, detail="Monitoring job not found")
    if job.status == "completed":
        return {"job_id": job.id, "status": job.status, "idempotent": True}
    run_prepared_imagery_job(session, job)
    return {"job_id": job.id, "status": job.status, "error_message": job.error_message}

@router.get("/watersheds/{watershed_id}/imagery")
def imagery_history(watershed_id: str, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.FIELD_WORKER, Role.SUPERVISOR, Role.AUDITOR, Role.VIEWER))) -> list[dict]:
    watershed_for(session, principal, watershed_id)
    rows = session.scalars(select(ImageryAcquisition).where(ImageryAcquisition.organisation_id == principal.organisation_id, ImageryAcquisition.watershed_id == watershed_id).order_by(ImageryAcquisition.acquired_at)).all()
    return [{"id": row.id, "source": row.provider, "acquisition_date": row.acquired_at.date().isoformat(), "cloud_percentage": row.cloud_percentage, "asset_key": row.asset_key, "quality_flags": row.quality_flags, "processing_status": row.processing_status, "data_status": row.data_status} for row in rows]

@router.get("/watersheds/{watershed_id}/indicators")
def indicator_series(watershed_id: str, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.FIELD_WORKER, Role.SUPERVISOR, Role.AUDITOR, Role.VIEWER))) -> list[dict]:
    watershed_for(session, principal, watershed_id)
    rows = session.execute(select(ImageryAcquisition, IndicatorObservation).join(IndicatorObservation, IndicatorObservation.acquisition_id == ImageryAcquisition.id).where(ImageryAcquisition.organisation_id == principal.organisation_id, ImageryAcquisition.watershed_id == watershed_id).order_by(ImageryAcquisition.acquired_at)).all()
    return [{"date": image.acquired_at.date().isoformat(), "ndvi": observation.ndvi, "ndwi": observation.ndwi, "source": image.provider, "confidence": observation.confidence, "summary": observation.observed_summary, "limitations": observation.limitations} for image, observation in rows]

@router.get("/alerts")
def list_alerts(session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.SUPERVISOR, Role.AUDITOR))) -> list[dict]:
    rows = session.scalars(select(MonitoringAlert).where(MonitoringAlert.organisation_id == principal.organisation_id, MonitoringAlert.status == "open").order_by(MonitoringAlert.created_at.desc())).all()
    return [{"id": row.id, "type": row.alert_type, "severity": row.severity, "message": row.message, "watershed_id": row.watershed_id} for row in rows]
