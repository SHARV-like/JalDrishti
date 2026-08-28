import json
from pathlib import Path

METADATA_FILE = Path(__file__).resolve().parents[3] / "data" / "images" / "demo-classifier-metadata.json"


def detect_intervention(filename: str | None, nearest_intervention: dict | None) -> dict:
    """Return a transparent, limited-scope demo assessment; no ML inference is claimed."""
    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    sample = metadata["samples"].get((filename or "").lower())
    if sample:
        label, confidence, explanation = sample["label"], sample["confidence"], sample["explanation"]
    else:
        label, confidence, explanation = "Unknown / Needs Review", 0, "This image is not one of the approved, labelled demo samples. A human review is required."

    type_map = {"Check Dam": "check_dam", "Farm Pond": "farm_pond"}
    expected_type = nearest_intervention.get("intervention_type") if nearest_intervention else None
    detected_type = type_map.get(label)
    if not expected_type:
        consistency = {"status": "Needs Review", "message": "No nearby registered intervention is available for a consistency check."}
    elif not detected_type:
        consistency = {"status": "Needs Review", "message": "The detected class cannot be compared to the nearby registered intervention."}
    elif detected_type == expected_type:
        consistency = {"status": "Consistent", "message": f"The detected {label.lower()} is consistent with the nearby registered {expected_type.replace('_', ' ')}."}
    else:
        consistency = {"status": "Inconsistent", "message": f"The detected {label.lower()} is not consistent with the nearby registered {expected_type.replace('_', ' ')}."}

    return {"label": label, "confidence": confidence, "explanation": explanation, "review_status": "Needs Review" if confidence < 80 or label == "Unknown / Needs Review" else "Demo Assessment", "method": metadata["method"], "caveat": metadata["caveat"], "consistency": consistency}
