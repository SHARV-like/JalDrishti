"""Explainable, versioned planning estimates. They are not engineering designs."""
from typing import Any

INTERVENTIONS = ("Contour Trench", "Farm Pond", "Check Dam", "Percolation Tank", "Recharge Pit", "Afforestation")
DEFAULT_WEIGHTS = {"slope": 0.12, "runoff": 0.22, "vegetation": 0.16, "terrain": 0.12, "drainage": 0.13, "rainfall": 0.1, "coverage": 0.07, "residual_risk": 0.08}

def normalise_conditions(conditions: dict[str, Any]) -> dict[str, float]:
    return {
        "slope": min(100, max(0, float(conditions.get("slope_deg", 5)) * 8)),
        "runoff": {"high": 95, "medium": 65, "low": 30}.get(str(conditions.get("runoff_proxy", "medium")).lower(), 50),
        "vegetation": {"sparse": 90, "moderate": 60, "dense": 25}.get(str(conditions.get("vegetation_condition", "moderate")).lower(), 50),
        "terrain": 80 if "loam" in str(conditions.get("terrain_soil_proxy", "")).lower() else 55,
        "drainage": 90 if float(conditions.get("distance_to_drainage_m", 300)) <= 250 else 55,
        "rainfall": min(100, max(0, float(conditions.get("rainfall_mm", 600)) / 12)),
        "coverage": min(100, max(0, float(conditions.get("existing_coverage", 20)))),
        "residual_risk": {"high": 95, "moderate": 65, "low": 30}.get(str(conditions.get("risk_level", "moderate")).lower(), 50),
    }

def score_scenarios(conditions: dict[str, Any], rules: dict[str, Any] | None = None) -> list[dict]:
    weights = (rules or {}).get("weights", DEFAULT_WEIGHTS)
    values = normalise_conditions(conditions)
    profiles = {"Contour Trench": {"slope": 1.2, "runoff": 1.1, "vegetation": 1.2}, "Farm Pond": {"runoff": 1.2, "terrain": 1.1, "rainfall": 1.1}, "Check Dam": {"drainage": 1.35, "runoff": 1.15}, "Percolation Tank": {"terrain": 1.25, "rainfall": 1.2, "drainage": .9}, "Recharge Pit": {"drainage": 1.15, "coverage": .7}, "Afforestation": {"vegetation": 1.35, "slope": 1.1, "residual_risk": 1.1}}
    results = []
    for name in INTERVENTIONS:
        score = sum(values[key] * float(weights.get(key, 0)) * profiles[name].get(key, 1) for key in weights)
        suitability = round(min(100, score))
        priority = "High" if suitability >= 75 else "Medium" if suitability >= 50 else "Low"
        results.append({"intervention": name, "suitability_score": suitability, "priority": priority, "evidence_factors": [f"{key.replace('_', ' ')}: {round(values[key])}" for key in sorted(weights, key=lambda item: values[item] * float(weights[item]), reverse=True)[:3]], "constraints": ["Site survey, land availability, hydrology, and engineering design remain required."], "assumptions": ["Scores are planning estimates based on configured pilot proxies."], "engineering_review_required": True})
    return sorted(results, key=lambda result: result["suitability_score"], reverse=True)
