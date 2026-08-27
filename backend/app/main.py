from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.watersheds import router as watersheds_router
from app.routes.field_evidence import router as field_evidence_router

app = FastAPI(title="JalDrishti API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])
app.include_router(watersheds_router, prefix="/api/v1")
app.include_router(field_evidence_router, prefix="/api/v1")

@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "analysis_version": "mvp-0.1"}
