from fastapi import APIRouter, HTTPException

from app.services.recommendations import rank_recommendations

router = APIRouter(tags=["recommendations"])

@router.get("/risk-zones/{zone_id}/recommendations")
def get_recommendations(zone_id: str) -> dict:
    try:
        return rank_recommendations(zone_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"code": "risk_zone_not_found", "message": "Risk zone was not found."}) from exc
