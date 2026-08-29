from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.watersheds import router as watersheds_router
from app.routes.recommendations import router as recommendations_router
from app.routes.field_evidence import router as field_evidence_router
from app.routes.impact_reports import router as impact_reports_router
from app.routes.production import router as production_router
from app.routes.operations import router as operations_router
from app.production.config import get_settings

settings = get_settings()
app = FastAPI(title="JalDrishti API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Development-User", "X-Organisation-Id"],
)
app.include_router(watersheds_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(field_evidence_router, prefix="/api/v1")
app.include_router(impact_reports_router, prefix="/api/v1")
app.include_router(production_router, prefix="/api/v1")
app.include_router(operations_router, prefix="/api/v1")

@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "analysis_version": "mvp-0.1"}
