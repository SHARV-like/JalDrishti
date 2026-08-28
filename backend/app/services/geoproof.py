from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import json

from shapely.geometry import Point, shape

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
        "gps_valid": 20 if input_data.gps_valid else 0,
        "inside_watershed": 45 if input_data.inside_watershed else 0,
        "intervention_proximity": 25 if input_data.within_intervention_buffer else 0,
        "timestamp_plausibility": 10 if input_data.timestamp_plausible else 0,
    }
    total = sum(components.values())
    verdict = "Verified" if total >= 80 else "Needs Review" if total >= 50 else "Location Mismatch"
    return {"total_score": total, "verdict": verdict, "components": components, "ruleset_version": "geoproof-mvp-0.2", "data_status": "demo"}


DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "geo"


def _distance_meters(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    """Great-circle distance in metres for two WGS84 latitude/longitude points."""
    earth_radius_m = 6_371_000
    delta_latitude = radians(latitude_b - latitude_a)
    delta_longitude = radians(longitude_b - longitude_a)
    haversine = sin(delta_latitude / 2) ** 2 + cos(radians(latitude_a)) * cos(radians(latitude_b)) * sin(delta_longitude / 2) ** 2
    return 2 * earth_radius_m * asin(sqrt(haversine))


def evaluate_location_geoproof(gps: dict | None, captured_at: str | None) -> dict:
    """Evaluate a GPS point against the committed demo watershed and intervention layers."""
    explanations: list[dict[str, str | int]] = []
    if not gps:
        return {"total_score": 0, "verdict": "Location Mismatch", "components": {"inside_watershed": 0, "intervention_proximity": 0, "gps_valid": 0, "capture_timestamp": 0}, "distance_to_nearest_intervention_m": None, "nearest_intervention": None, "explanations": [{"factor": "GPS metadata", "points": 0, "message": "No valid GPS metadata was available, so location verification cannot be completed."}, {"factor": "Capture timestamp", "points": 10 if captured_at else 0, "message": "A capture timestamp is available." if captured_at else "No capture timestamp was available."}], "ruleset_version": "geoproof-mvp-0.2", "data_status": "demo"}

    latitude, longitude = gps["latitude"], gps["longitude"]
    gps_valid = -90 <= latitude <= 90 and -180 <= longitude <= 180
    boundary_data = json.loads((DATA_DIR / "watersheds.geojson").read_text(encoding="utf-8"))
    intervention_data = json.loads((DATA_DIR / "interventions.geojson").read_text(encoding="utf-8"))
    watershed = shape(boundary_data["features"][0]["geometry"])
    location = Point(longitude, latitude)
    inside = gps_valid and watershed.covers(location)
    nearest = min(intervention_data["features"], key=lambda feature: _distance_meters(latitude, longitude, feature["geometry"]["coordinates"][1], feature["geometry"]["coordinates"][0]))
    nearest_longitude, nearest_latitude = nearest["geometry"]["coordinates"]
    distance_m = round(_distance_meters(latitude, longitude, nearest_latitude, nearest_longitude), 1)
    within_buffer = distance_m <= 150
    components = {"inside_watershed": 45 if inside else 0, "intervention_proximity": 25 if within_buffer else 0, "gps_valid": 20 if gps_valid else 0, "capture_timestamp": 10 if captured_at else 0}
    total = sum(components.values())
    verdict = "Verified" if total >= 80 else "Needs Review" if total >= 50 else "Location Mismatch"
    explanations.extend([
        {"factor": "GPS metadata", "points": components["gps_valid"], "message": "Valid latitude and longitude were extracted from the image." if gps_valid else "The extracted coordinates are outside valid WGS84 ranges."},
        {"factor": "Watershed boundary", "points": components["inside_watershed"], "message": "The uploaded-photo location lies inside the selected watershed boundary." if inside else "The uploaded-photo location lies outside the selected watershed boundary."},
        {"factor": "Nearest intervention", "points": components["intervention_proximity"], "message": f"The nearest registered intervention is {distance_m:.1f} m away." + (" This is within the 150 m review buffer." if within_buffer else " This is outside the 150 m review buffer.")},
        {"factor": "Capture timestamp", "points": components["capture_timestamp"], "message": "A capture timestamp is available." if captured_at else "No capture timestamp was available."},
    ])
    return {"total_score": total, "verdict": verdict, "components": components, "distance_to_nearest_intervention_m": distance_m, "nearest_intervention": {"id": nearest["properties"]["id"], "name": nearest["properties"].get("name", "Registered intervention"), "intervention_type": nearest["properties"].get("intervention_type"), "status": nearest["properties"].get("status"), "latitude": nearest_latitude, "longitude": nearest_longitude}, "explanations": explanations, "ruleset_version": "geoproof-mvp-0.2", "data_status": "demo"}
