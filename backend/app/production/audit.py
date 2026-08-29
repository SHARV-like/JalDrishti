from sqlalchemy.orm import Session

from app.production.models import AuditEvent


def record_audit(session: Session, organisation_id: str, actor_id: str | None, action: str, entity_type: str, entity_id: str, details: dict | None = None) -> None:
    session.add(AuditEvent(organisation_id=organisation_id, actor_id=actor_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details or {}))
