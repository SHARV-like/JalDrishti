from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.production.audit import record_audit
from app.production.auth import Principal, require_roles
from app.production.database import get_session
from app.production.models import Intervention, MonitoringAlert, RecommendationRuleset, RecommendationRun, RiskZone, Role, VerificationReview, Watershed
from app.services.planning import DEFAULT_WEIGHTS, score_scenarios

router = APIRouter(prefix="/planning", tags=["planning and dashboards"])

class RulesetInput(BaseModel):
    region_key: str = Field(min_length=2, max_length=120)
    version: str = Field(min_length=1, max_length=80)
    weights: dict[str, float] = Field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    assumptions: list[str] = Field(default_factory=list, max_length=20)

class ScenarioInput(BaseModel):
    ruleset_id: str
    overrides: dict[str, float | str] = Field(default_factory=dict)

def zone_for(session: Session, principal: Principal, zone_id: str) -> RiskZone:
    zone = session.get(RiskZone, zone_id)
    if not zone or zone.organisation_id != principal.organisation_id:
        raise HTTPException(status_code=404, detail="Risk zone not found in this organisation")
    return zone

@router.post("/rulesets", status_code=status.HTTP_201_CREATED)
def create_ruleset(payload: RulesetInput, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN))) -> dict:
    if any(value < 0 or value > 1 for value in payload.weights.values()) or not 0.95 <= sum(payload.weights.values()) <= 1.05:
        raise HTTPException(status_code=422, detail="Rule weights must be between 0 and 1 and total approximately 1.")
    item = RecommendationRuleset(organisation_id=principal.organisation_id, region_key=payload.region_key, version=payload.version, rules={"weights": payload.weights}, assumptions=payload.assumptions, created_by=principal.user_id)
    session.add(item); session.flush(); record_audit(session, principal.organisation_id, principal.user_id, "ruleset_created", "recommendation_ruleset", item.id)
    return {"id": item.id, "version": item.version}

@router.post("/risk-zones/{zone_id}/scenarios", status_code=status.HTTP_201_CREATED)
def create_scenario(zone_id: str, payload: ScenarioInput, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.SUPERVISOR, Role.AUDITOR))) -> dict:
    zone = zone_for(session, principal, zone_id)
    ruleset = session.get(RecommendationRuleset, payload.ruleset_id)
    if not ruleset or ruleset.organisation_id != principal.organisation_id or not ruleset.active:
        raise HTTPException(status_code=404, detail="Active ruleset not found in this organisation")
    inputs = {**zone.conditions, **payload.overrides, "risk_level": zone.risk_level}
    results = score_scenarios(inputs, ruleset.rules)
    run = RecommendationRun(organisation_id=principal.organisation_id, watershed_id=zone.watershed_id, risk_zone_id=zone.id, ruleset_id=ruleset.id, ruleset_version=ruleset.version, inputs=inputs, results=results, created_by=principal.user_id)
    session.add(run); session.flush(); record_audit(session, principal.organisation_id, principal.user_id, "scenario_created", "recommendation_run", run.id)
    return {"id": run.id, "status": "estimate", "ruleset_version": run.ruleset_version, "recommended_next_action": results[0], "alternatives": results[1:], "disclaimer": "Planning estimate only; field survey and engineering approval are mandatory."}

@router.get("/dashboard")
def dashboard(watershed_id: str | None = None, village_id: str | None = None, intervention_type: str | None = None, intervention_status: str | None = None, verification_status: str | None = None, risk_level: str | None = None, session: Session = Depends(get_session), principal: Principal = Depends(require_roles(Role.ADMIN, Role.SUPERVISOR, Role.AUDITOR, Role.VIEWER))) -> dict:
    interventions = select(Intervention).where(Intervention.organisation_id == principal.organisation_id)
    if watershed_id: interventions = interventions.where(Intervention.watershed_id == watershed_id)
    if village_id: interventions = interventions.where(Intervention.village_id == village_id)
    if intervention_type: interventions = interventions.where(Intervention.intervention_type == intervention_type)
    if intervention_status: interventions = interventions.where(Intervention.lifecycle_status == intervention_status)
    items = session.scalars(interventions).all()
    zones = select(RiskZone).where(RiskZone.organisation_id == principal.organisation_id)
    if watershed_id: zones = zones.where(RiskZone.watershed_id == watershed_id)
    if risk_level: zones = zones.where(RiskZone.risk_level == risk_level)
    zone_rows = session.scalars(zones).all()
    backlog = session.scalars(select(VerificationReview).where(VerificationReview.organisation_id == principal.organisation_id, VerificationReview.outcome == "needs_review")).all()
    alerts = session.scalars(select(MonitoringAlert).where(MonitoringAlert.organisation_id == principal.organisation_id, MonitoringAlert.status == "open")).all()
    return {"filters": {"watershed_id": watershed_id, "village_id": village_id, "intervention_type": intervention_type, "intervention_status": intervention_status, "verification_status": verification_status, "risk_level": risk_level}, "intervention_progress": {"total": len(items), "verified": sum(item.lifecycle_status == "verified" for item in items), "submitted": sum(item.lifecycle_status == "submitted" for item in items)}, "verification_backlog": len(backlog), "high_priority_risk_zones": sum(zone.risk_level == "high" for zone in zone_rows), "pending_alerts": len(alerts), "observed_environmental_trends_note": "Use the monitoring indicator-series endpoint; all values are observed/pilot indicators, not causal proof."}
