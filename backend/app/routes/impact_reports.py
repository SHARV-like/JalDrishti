from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.impact_report import build_impact_report

router = APIRouter(tags=["impact reports"])


@router.get("/intervention-sites/{site_id}/impact-report")
def download_impact_report(site_id: str) -> Response:
    report = build_impact_report(site_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Pilot intervention site not found")
    return Response(
        content=report,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="jaldirshti-impact-report-{site_id}.pdf"'},
    )
