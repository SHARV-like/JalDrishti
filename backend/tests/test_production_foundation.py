from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.production.database import Base, get_session
from app.production.models import Intervention, Membership, Role, User
from app.production.seed import DEMO_ADMIN_ID, seed_mvp_demo


def build_seeded_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory.begin() as session:
        result = seed_mvp_demo(session)
    return session_factory, result


def test_demo_seed_is_idempotent():
    session_factory, initial = build_seeded_session()
    assert initial["watersheds_created"] == 1
    assert initial["interventions_created"] == 5
    with session_factory.begin() as session:
        repeated = seed_mvp_demo(session)
        assert repeated["watersheds_created"] == 0
        assert repeated["interventions_created"] == 0
        assert len(session.scalars(select(Intervention)).all()) == 5


def test_org_scoped_intervention_and_evidence_intent():
    session_factory, seed = build_seeded_session()

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
    headers = {"X-Development-User": DEMO_ADMIN_ID, "X-Organisation-Id": seed["organisation_id"]}
    try:
        with TestClient(app) as client:
            listed = client.get("/api/v1/production/interventions", headers=headers)
            assert listed.status_code == 200
            intervention = listed.json()[0]

            evidence = client.post(
                f"/api/v1/production/interventions/{intervention['id']}/evidence-intents",
                headers=headers,
                json={"filename": "check-dam.jpg", "content_type": "image/jpeg", "size_bytes": 1024},
            )
            assert evidence.status_code == 201
            assert evidence.json()["object_key"].startswith(f"organisations/{seed['organisation_id']}/evidence/")
            assert evidence.json()["upload_url"] is None
    finally:
        app.dependency_overrides.clear()


def test_field_worker_cannot_verify_an_intervention():
    session_factory, seed = build_seeded_session()
    with session_factory.begin() as session:
        worker = User(id="field-worker", display_name="Field worker")
        session.add(worker)
        session.add(Membership(organisation_id=seed["organisation_id"], user_id=worker.id, role=Role.FIELD_WORKER.value))
        intervention = session.scalars(select(Intervention)).first()
        intervention.lifecycle_status = "submitted"
        intervention_id = intervention.id

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
    headers = {"X-Development-User": "field-worker", "X-Organisation-Id": seed["organisation_id"]}
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/production/interventions/{intervention_id}/transition",
                headers=headers,
                json={"to_status": "verified", "reason": "Attempted field verification"},
            )
            assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
