import json
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.production.audit import record_audit
from app.production.config import PROJECT_ROOT
from app.production.models import Intervention, InterventionEvent, LifecycleStatus, Membership, Organisation, Role, User, Watershed


DEMO_ORGANISATION_SLUG = "jaldirshti-demo"
DEMO_ADMIN_ID = "demo-admin"


def seed_mvp_demo(session: Session) -> dict[str, int | str]:
    organisation = session.scalar(select(Organisation).where(Organisation.slug == DEMO_ORGANISATION_SLUG))
    if not organisation:
        organisation = Organisation(slug=DEMO_ORGANISATION_SLUG, name="JalDrishti MVP Demo Organisation")
        session.add(organisation); session.flush()
    if not session.get(User, DEMO_ADMIN_ID):
        session.add(User(id=DEMO_ADMIN_ID, display_name="Demo administrator"))
    if not session.scalar(select(Membership).where(Membership.organisation_id == organisation.id, Membership.user_id == DEMO_ADMIN_ID)):
        session.add(Membership(organisation_id=organisation.id, user_id=DEMO_ADMIN_ID, role=Role.ADMIN.value))
    watershed_data = json.loads((PROJECT_ROOT / "data/geo/watersheds.geojson").read_text(encoding="utf-8"))
    intervention_data = json.loads((PROJECT_ROOT / "data/geo/interventions.geojson").read_text(encoding="utf-8"))
    watershed_count = intervention_count = 0
    for feature in watershed_data["features"]:
        props = feature["properties"]; external_id = props.get("id", props.get("watershed_id", "demo-watershed"))
        watershed = session.scalar(select(Watershed).where(Watershed.organisation_id == organisation.id, Watershed.external_id == external_id))
        if not watershed:
            watershed = Watershed(organisation_id=organisation.id, external_id=external_id, name=props.get("name", "Demo watershed"), geojson=feature["geometry"], data_status="demo", source_attribution=props.get("provenance", {})); session.add(watershed); session.flush(); watershed_count += 1
        for item in [entry for entry in intervention_data["features"] if entry["properties"].get("watershed_id") == external_id]:
            item_props = item["properties"]; item_id = item_props["id"]
            intervention = session.scalar(select(Intervention).where(Intervention.organisation_id == organisation.id, Intervention.external_id == item_id))
            if not intervention:
                status_value = item_props.get("status", "planned").lower().replace(" ", "_")
                if status_value not in {state.value for state in LifecycleStatus}: status_value = LifecycleStatus.PLANNED.value
                intervention = Intervention(organisation_id=organisation.id, watershed_id=watershed.id, external_id=item_id, name=item_props.get("name", item_id), intervention_type=item_props.get("intervention_type", "unknown"), lifecycle_status=status_value, geometry=item["geometry"], data_status="demo", source_attribution=item_props.get("provenance", {})); session.add(intervention); session.flush()
                session.add(InterventionEvent(organisation_id=organisation.id, intervention_id=intervention.id, from_status=None, to_status=status_value, reason="Imported from MVP demo data", actor_id=DEMO_ADMIN_ID)); intervention_count += 1
    if session.bind and session.bind.dialect.name == "postgresql":
        session.execute(text("""
            UPDATE watersheds
            SET geom = ST_SetSRID(ST_GeomFromGeoJSON(CAST(geojson AS text)), 4326)
            WHERE organisation_id = :organisation_id AND geom IS NULL
        """), {"organisation_id": organisation.id})
        session.execute(text("""
            UPDATE interventions
            SET geom = ST_SetSRID(ST_GeomFromGeoJSON(CAST(geometry AS text)), 4326)
            WHERE organisation_id = :organisation_id AND geom IS NULL
        """), {"organisation_id": organisation.id})
    if watershed_count or intervention_count:
        record_audit(session, organisation.id, DEMO_ADMIN_ID, "demo_seeded", "organisation", organisation.id, {"watersheds_created": watershed_count, "interventions_created": intervention_count})
    return {"organisation_id": organisation.id, "organisation_slug": organisation.slug, "watersheds_created": watershed_count, "interventions_created": intervention_count}
