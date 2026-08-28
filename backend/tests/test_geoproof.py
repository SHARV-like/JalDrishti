from app.services.geoproof import GeoProofInput, evaluate_location_geoproof, score_geoproof

def test_geoproof_returns_a_traceable_verified_result() -> None:
    result = score_geoproof(GeoProofInput(True, True, True, True, True))
    assert result["total_score"] == 100
    assert result["verdict"] == "Verified"
    assert result["ruleset_version"] == "geoproof-mvp-0.2"


def test_inside_boundary_location_is_verified_when_near_intervention() -> None:
    result = evaluate_location_geoproof({"latitude": 19.006, "longitude": 73.007}, "2026-08-28T09:30:00")
    assert result["total_score"] == 100
    assert result["verdict"] == "Verified"
    assert result["distance_to_nearest_intervention_m"] == 0


def test_outside_boundary_location_is_location_mismatch() -> None:
    result = evaluate_location_geoproof({"latitude": 19.03, "longitude": 73.03}, "2026-08-28T09:30:00")
    assert result["total_score"] == 30
    assert result["verdict"] == "Location Mismatch"
