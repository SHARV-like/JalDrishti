from dataclasses import dataclass

@dataclass(frozen=True)
class GeoProofInput:
    gps_valid: bool
    inside_watershed: bool
    within_intervention_buffer: bool
    timestamp_plausible: bool
    image_context_supported: bool

def score_geoproof(input_data: GeoProofInput) -> dict:
    """MVP assumption-based score; it is not a fraud or causal determination."""
    components = {
        "gps_valid": 25 if input_data.gps_valid else 0,
        "inside_watershed": 25 if input_data.inside_watershed else 0,
        "intervention_proximity": 20 if input_data.within_intervention_buffer else 0,
        "timestamp_plausibility": 10 if input_data.timestamp_plausible else 0,
        "image_context": 20 if input_data.image_context_supported else 0,
    }
    total = sum(components.values())
    verdict = "verified" if total >= 80 else "needs_review" if total >= 50 else "not_verified"
    return {"total_score": total, "verdict": verdict, "components": components, "ruleset_version": "geoproof-mvp-0.1", "data_status": "demo"}
