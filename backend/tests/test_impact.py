from app.services.impact import calculate_impact


def test_impact_score_has_transparent_weighted_factors() -> None:
    result = calculate_impact(75, "completed")
    assert result["score"] == 85
    assert [factor["name"] for factor in result["factors"]] == ["GeoProof", "Vegetation response", "Water response", "Intervention completion"]
    assert "season" in result["limitation"]
