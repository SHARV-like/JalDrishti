from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.production.models import ImageryAcquisition, IndicatorObservation, MonitoringAlert, MonitoringJob, Watershed
from app.services.monitoring import PreparedPilotAdapter, observed_change_summary


def run_prepared_imagery_job(session: Session, job: MonitoringJob) -> MonitoringJob:
    """Idempotent worker entry point for the offline pilot provider."""
    try:
        job.status, job.attempts = "running", job.attempts + 1
        watershed = session.get(Watershed, job.watershed_id)
        if not watershed:
            raise ValueError("Watershed is unavailable")
        candidates = PreparedPilotAdapter().catalogue(job.watershed_id)
        acquisitions = []
        for candidate in candidates:
            record = session.scalar(select(ImageryAcquisition).where(ImageryAcquisition.organisation_id == job.organisation_id, ImageryAcquisition.external_id == candidate.external_id))
            if not record:
                record = ImageryAcquisition(organisation_id=job.organisation_id, watershed_id=job.watershed_id, intervention_id=job.intervention_id, external_id=candidate.external_id, provider=candidate.provider, acquired_at=candidate.acquired_at, cloud_percentage=candidate.cloud_percentage, coverage_geojson=watershed.geojson, processing_status="ready", quality_flags=[] if (candidate.cloud_percentage or 0) <= 20 else ["cloudy"], asset_key=candidate.asset_key, source_attribution={"offline": True}, data_status="pilot")
                session.add(record); session.flush()
                session.add(MonitoringAlert(organisation_id=job.organisation_id, watershed_id=job.watershed_id, intervention_id=job.intervention_id, alert_type="usable_imagery", severity="info", message=f"Usable prepared pilot imagery is available for {candidate.acquired_at.date()}."))
            if not session.scalar(select(IndicatorObservation).where(IndicatorObservation.acquisition_id == record.id)):
                session.add(IndicatorObservation(organisation_id=job.organisation_id, acquisition_id=record.id, ndvi=candidate.ndvi, ndwi=candidate.ndwi, observed_summary="Prepared pilot indicator. It is not observed live satellite evidence.", confidence="pilot", limitations=candidate.limitations))
            acquisitions.append((record, candidate))
        if len(acquisitions) >= 2:
            before, after = sorted(acquisitions, key=lambda pair: pair[1].acquired_at)[:2]
            summary = observed_change_summary(before[1], after[1])
            change = (after[1].ndvi or 0) - (before[1].ndvi or 0)
            if abs(change) >= 0.1:
                session.add(MonitoringAlert(organisation_id=job.organisation_id, watershed_id=job.watershed_id, intervention_id=job.intervention_id, alert_type="indicator_change", severity="info" if change > 0 else "warning", message=summary))
        job.status, job.error_message, job.completed_at = "completed", None, datetime.now(timezone.utc)
    except Exception as exc:
        job.status, job.error_message = "failed", str(exc)
    return job
