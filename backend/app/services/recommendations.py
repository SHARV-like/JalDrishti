import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "geo" / "risk-zones.geojson"


def _runoff(value: str) -> int:
    return {"high": 95, "medium": 70, "low": 30}[value]


def rank_recommendations(zone_id: str) -> dict:
    zones = json.loads(DATA_FILE.read_text(encoding="utf-8"))["features"]
    zone = next((feature for feature in zones if feature["properties"]["id"] == zone_id), None)
    if not zone:
        raise KeyError(zone_id)
    conditions = zone["properties"]["conditions"]
    slope, runoff, vegetation, terrain, drainage = conditions["slope_deg"], _runoff(conditions["runoff_proxy"]), conditions["vegetation_condition"], conditions["terrain_soil_proxy"], conditions["distance_to_drainage_m"]
    contour = round(0.30 * (90 if 3 <= slope <= 12 else 45) + 0.30 * runoff + 0.20 * {"sparse": 90, "moderate": 65, "dense": 30}[vegetation] + 0.20 * (90 if "undulating" in terrain else 65))
    pond = round(0.25 * (90 if slope <= 5 else 45) + 0.35 * runoff + 0.20 * (85 if "loam" in terrain else 70) + 0.20 * (85 if drainage >= 250 else 55))
    dam = round(0.20 * (85 if slope <= 8 else 45) + 0.30 * runoff + 0.20 * (95 if drainage <= 250 else 40) + 0.30 * (85 if "loam" in terrain else 70))
    options = [
        {"intervention": "Contour Trench", "score": contour, "reasons": [f"Slope is {slope}°, within the contour-trench pilot range." if 3 <= slope <= 12 else f"Slope is {slope}°, outside the preferred contour-trench pilot range.", f"Runoff proxy is {conditions['runoff_proxy']}; vegetation is {vegetation}."]},
        {"intervention": "Farm Pond", "score": pond, "reasons": [f"Slope is {slope}° and drainage is {drainage} m away.", f"Runoff proxy is {conditions['runoff_proxy']} with {terrain} terrain/soil proxy."]},
        {"intervention": "Check Dam", "score": dam, "reasons": [f"Registered drainage distance is {drainage} m.", f"Runoff proxy is {conditions['runoff_proxy']} with {terrain} terrain/soil proxy."]},
    ]
    ranked = sorted(options, key=lambda item: item["score"], reverse=True)
    return {"risk_zone": {"id": zone_id, "name": zone["properties"]["name"], "risk_level": zone["properties"]["risk_level"], "conditions": conditions, "data_status": "demo"}, "recommendations": ranked, "recommended_next_action": ranked[0], "disclaimer": "Decision support only: final intervention selection requires field survey and engineering approval.", "ruleset_version": "recommendation-mvp-0.1"}
