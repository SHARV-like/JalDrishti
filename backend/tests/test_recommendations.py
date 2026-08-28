from app.services.recommendations import rank_recommendations


def test_every_demo_risk_zone_has_ranked_recommendations_and_disclaimer() -> None:
    expected_actions = {"demo-risk-001": "Contour Trench", "demo-risk-002": "Farm Pond", "demo-risk-003": "Check Dam"}
    for zone_id, expected_action in expected_actions.items():
        result = rank_recommendations(zone_id)
        assert len(result["recommendations"]) == 3
        assert result["recommended_next_action"]["intervention"] == expected_action
        assert result["recommendations"] == sorted(result["recommendations"], key=lambda item: item["score"], reverse=True)
        assert "engineering approval" in result["disclaimer"]
