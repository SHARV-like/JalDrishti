def calculate_impact(geoproof_score: int, intervention_status: str | None) -> dict:
    """Precomputed pilot indicator; transparent weights, not a causal conclusion."""
    vegetation_response, water_response = 86, 81
    completion_score = 100 if intervention_status in {"completed", "verified"} else 50 if intervention_status == "planned" else 0
    factors = [
        {"name": "GeoProof", "value": geoproof_score, "weight": 0.25, "contribution": round(geoproof_score * 0.25, 1), "explanation": "Location-verification score from the uploaded field evidence."},
        {"name": "Vegetation response", "value": vegetation_response, "weight": 0.30, "contribution": round(vegetation_response * 0.30, 1), "explanation": "Precomputed pilot NDVI response, labelled demo."},
        {"name": "Water response", "value": water_response, "weight": 0.25, "contribution": round(water_response * 0.25, 1), "explanation": "Precomputed pilot NDWI response, labelled demo."},
        {"name": "Intervention completion", "value": completion_score, "weight": 0.20, "contribution": round(completion_score * 0.20, 1), "explanation": "Registered intervention status in the prepared demo layer."},
    ]
    return {"score": round(sum(factor["contribution"] for factor in factors)), "classification": "Positive indicator" if sum(factor["contribution"] for factor in factors) >= 70 else "Needs review", "factors": factors, "data_status": "demo", "interpretation": "Vegetation and water retention indicators improved in this prepared pilot comparison.", "limitation": "Satellite-index changes can also be influenced by season, rainfall, cloud cover, and crop cycles. This pilot indicator does not establish causality."}
