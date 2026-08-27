from app.services.geoproof import GeoProofInput, score_geoproof

def test_geoproof_returns_a_traceable_verified_result() -> None:
    result = score_geoproof(GeoProofInput(True, True, True, True, True))
    assert result["total_score"] == 100
    assert result["verdict"] == "verified"
    assert result["ruleset_version"] == "geoproof-mvp-0.1"
