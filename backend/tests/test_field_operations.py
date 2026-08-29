from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.production.database import Base, get_session
from app.production.models import Intervention, Membership, Organisation, Role, User
from app.production.seed import DEMO_ADMIN_ID, seed_mvp_demo


def setup_api():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory.begin() as session:
        seed = seed_mvp_demo(session)
        session.add_all([User(id="worker", display_name="Field Worker"), User(id="supervisor", display_name="Supervisor")])
        session.add_all([
            Membership(organisation_id=seed["organisation_id"], user_id="worker", role=Role.FIELD_WORKER.value),
            Membership(organisation_id=seed["organisation_id"], user_id="supervisor", role=Role.SUPERVISOR.value),
        ])
        intervention = session.scalars(select(Intervention)).first()
        intervention.lifecycle_status = "completed"
        intervention_id, geometry = intervention.id, intervention.geometry

    def override_session():
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_session
    return seed, intervention_id, geometry, session_factory


def headers(user_id: str, organisation_id: str) -> dict[str, str]:
    return {"X-Development-User": user_id, "X-Organisation-Id": organisation_id}


def test_field_worker_evidence_submission_and_supervisor_approval():
    seed, intervention_id, geometry, _ = setup_api()
    try:
        with TestClient(app) as client:
            field_headers = headers("worker", seed["organisation_id"])
            intent = client.post(
                f"/api/v1/production/interventions/{intervention_id}/evidence-intents",
                headers=field_headers,
                json={"filename": "site.jpg", "content_type": "image/jpeg", "size_bytes": 5000},
            )
            assert intent.status_code == 201
            longitude, latitude = geometry["coordinates"]
            evidence = client.post(
                f"/api/v1/operations/evidence/{intent.json()['evidence_id']}/complete",
                headers=field_headers,
                json={"capture_time": "2026-08-30T09:00:00Z", "latitude": latitude, "longitude": longitude, "gps_accuracy_m": 8, "device_source": "approved demo device", "image_sha256": "a" * 64},
            )
            assert evidence.status_code == 200
            assert evidence.json()["geoproof_score"] >= 80
            assert "decision support" in evidence.json()["decision_support_note"]
            submitted = client.post(
                f"/api/v1/operations/interventions/{intervention_id}/submit",
                headers=field_headers,
                json={"comments": "Field evidence submitted for review", "assigned_to": "supervisor"},
            )
            assert submitted.status_code == 200
            supervisor_headers = headers("supervisor", seed["organisation_id"])
            queue = client.get("/api/v1/operations/reviews/queue", headers=supervisor_headers)
            assert queue.status_code == 200
            decision = client.post(
                f"/api/v1/operations/reviews/{submitted.json()['review_id']}",
                headers=supervisor_headers,
                json={"outcome": "approved", "comments": "GPS, timestamp, and site context are sufficient."},
            )
            assert decision.status_code == 200
            assert decision.json()["intervention_status"] == "verified"
    finally:
        app.dependency_overrides.clear()


def test_low_confidence_or_duplicate_evidence_requires_review():
    seed, intervention_id, _, _ = setup_api()
    try:
        with TestClient(app) as client:
            field_headers = headers("worker", seed["organisation_id"])
            first = client.post(f"/api/v1/production/interventions/{intervention_id}/evidence-intents", headers=field_headers, json={"filename": "first.jpg", "content_type": "image/jpeg", "size_bytes": 2000})
            client.post(f"/api/v1/operations/evidence/{first.json()['evidence_id']}/complete", headers=field_headers, json={"image_sha256": "b" * 64})
            second = client.post(f"/api/v1/production/interventions/{intervention_id}/evidence-intents", headers=field_headers, json={"filename": "second.jpg", "content_type": "image/jpeg", "size_bytes": 2000})
            completed = client.post(f"/api/v1/operations/evidence/{second.json()['evidence_id']}/complete", headers=field_headers, json={"image_sha256": "b" * 64})
            assert completed.status_code == 200
            assert completed.json()["review_status"] == "needs_review"
            assert any("duplicate" in warning.lower() for warning in completed.json()["warnings"])
    finally:
        app.dependency_overrides.clear()


def test_cross_organisation_access_is_rejected():
    seed, intervention_id, _, session_factory = setup_api()
    try:
        with TestClient(app) as client:
            with session_factory.begin() as session:
                other = Organisation(slug="other", name="Other organisation")
                session.add(other); session.flush()
                session.add(Membership(organisation_id=other.id, user_id=DEMO_ADMIN_ID, role=Role.ADMIN.value))
                other_id = other.id
            response = client.get(f"/api/v1/production/interventions", headers=headers(DEMO_ADMIN_ID, other_id))
            assert response.status_code == 200
            assert all(row["id"] != intervention_id for row in response.json())
    finally:
        app.dependency_overrides.clear()
