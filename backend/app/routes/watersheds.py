import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["watersheds"])
DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "geo" / "watersheds.geojson"

@router.get("/watersheds")
def list_watersheds() -> list[dict]:
    """Return prepared GeoJSON features as traceable watershed resources."""
    collection = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return [
        {"id": feature["properties"]["id"], "name": feature["properties"]["name"], "data_status": feature["properties"]["data_status"], "provenance": feature["properties"]["provenance"]}
        for feature in collection["features"]
    ]
