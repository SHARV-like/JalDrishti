from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.exif import ALLOWED_CONTENT_TYPES, MAX_IMAGE_BYTES, extract_image_metadata
from app.services.geoproof import evaluate_location_geoproof
from app.services.intervention_detection import detect_intervention
from app.services.impact import calculate_impact

router = APIRouter(tags=["field-evidence"])


@router.post("/field-evidence")
async def inspect_field_evidence(file: UploadFile = File(...)) -> dict:
    """Inspect an image in memory. Files are never written to disk or external storage."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail={"code": "unsupported_file_type", "message": "Upload a JPEG or PNG image."})

    content = await file.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail={"code": "file_too_large", "message": "Image must be 10 MB or smaller."})

    try:
        metadata = extract_image_metadata(content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "invalid_image", "message": str(exc)}) from exc

    geoproof = evaluate_location_geoproof(metadata["gps"], metadata["captured_at"])
    return {
        "id": "local-inspection",
        "data_status": "demo",
        "provenance": {"source_type": "local_upload", "method": "in-memory EXIF inspection", "storage": "not persisted"},
        "original_filename": file.filename,
        "metadata": metadata,
        "geoproof": geoproof,
        "visual_assessment": detect_intervention(file.filename, geoproof["nearest_intervention"]),
        "impact_assessment": calculate_impact(geoproof["total_score"], geoproof["nearest_intervention"]["status"] if geoproof["nearest_intervention"] else None),
        "review_message": None if metadata["gps"] else "No GPS metadata found — manual review required.",
    }
