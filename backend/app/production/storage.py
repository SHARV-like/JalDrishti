import uuid
from dataclasses import dataclass

from app.production.config import get_settings


ALLOWED_EVIDENCE_TYPES = {"image/jpeg", "image/png"}


@dataclass(frozen=True)
class UploadIntent:
    object_key: str
    upload_url: str | None
    expires_in_seconds: int


def create_upload_intent(organisation_id: str, evidence_id: str, content_type: str, size_bytes: int) -> UploadIntent:
    settings = get_settings()
    if content_type not in ALLOWED_EVIDENCE_TYPES:
        raise ValueError("Only JPEG and PNG evidence files are allowed")
    if size_bytes <= 0 or size_bytes > settings.max_evidence_bytes:
        raise ValueError(f"Evidence must be between 1 byte and {settings.max_evidence_bytes} bytes")
    key = f"organisations/{organisation_id}/evidence/{evidence_id}/{uuid.uuid4()}"
    # Phase 1 exposes the object key only for local/development storage. Production adapters return a signed PUT URL.
    return UploadIntent(object_key=key, upload_url=None, expires_in_seconds=900)
