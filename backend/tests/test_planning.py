from app.services.planning import INTERVENTIONS, score_scenarios

def test_scenarios_rank_all_supported_interventions_with_review_note():
    results = score_scenarios({"slope_deg": 7, "runoff_proxy": "high", "vegetation_condition": "sparse", "terrain_soil_proxy": "loam", "distance_to_drainage_m": 120, "rainfall_mm": 800, "existing_coverage": 25, "risk_level": "high"})
    assert {item["intervention"] for item in results} == set(INTERVENTIONS)
    assert results[0]["suitability_score"] >= results[-1]["suitability_score"]
    assert all(item["engineering_review_required"] for item in results)
