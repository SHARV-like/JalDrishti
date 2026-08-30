from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.production.database import Base, get_session
from app.production.models import Watershed
from app.production.seed import DEMO_ADMIN_ID, seed_mvp_demo


def test_prepared_monitoring_job_is_idempotent_and_returns_series():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory.begin() as session:
        seed = seed_mvp_demo(session)
        watershed_id = session.scalars(select(Watershed)).first().id
    def override():
        session = session_factory()
        try:
            yield session; session.commit()
        except Exception:
            session.rollback(); raise
        finally:
            session.close()
    app.dependency_overrides[get_session] = override
    headers = {"X-Development-User": DEMO_ADMIN_ID, "X-Organisation-Id": seed["organisation_id"]}
    try:
        with TestClient(app) as client:
            queued = client.post(f"/api/v1/monitoring/watersheds/{watershed_id}/prepared-ingest", headers=headers, json={"idempotency_key": "pilot-ingest-001"})
            assert queued.status_code == 202
            ran = client.post(f"/api/v1/monitoring/jobs/{queued.json()['job_id']}/run", headers=headers)
            assert ran.json()["status"] == "completed"
            rerun = client.post(f"/api/v1/monitoring/jobs/{queued.json()['job_id']}/run", headers=headers)
            assert rerun.json()["idempotent"] is True
            series = client.get(f"/api/v1/monitoring/watersheds/{watershed_id}/indicators", headers=headers)
            assert series.status_code == 200 and len(series.json()) == 2
            assert "not observed live" in series.json()[0]["summary"]
            alerts = client.get("/api/v1/monitoring/alerts", headers=headers)
            assert len(alerts.json()) >= 2
    finally:
        app.dependency_overrides.clear()
