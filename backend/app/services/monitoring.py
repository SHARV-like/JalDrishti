"""Provider-neutral monitoring contracts and offline prepared-asset adapter."""
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ImageryCandidate:
    external_id: str
    provider: str
    acquired_at: datetime
    cloud_percentage: float | None
    asset_key: str
    ndvi: float | None
    ndwi: float | None
    limitations: str


class ImageryProvider(Protocol):
    name: str
    def catalogue(self, watershed_id: str) -> list[ImageryCandidate]: ...


class WeatherProvider(Protocol):
    name: str
    def observations(self, watershed_id: str, start: datetime, end: datetime) -> list[dict]: ...


class PreparedPilotAdapter:
    """Offline adapter; intentionally makes no network call and requires no key."""
    name = "prepared-pilot"

    def catalogue(self, watershed_id: str) -> list[ImageryCandidate]:
        metadata = json.loads((Path(__file__).resolve().parents[3] / "data/satellite/metadata.json").read_text(encoding="utf-8"))
        limitations = metadata["limitations"]
        return [
            ImageryCandidate(f"pilot-{period}", self.name, datetime.fromisoformat(value["date"] + "T00:00:00+00:00"), 0.0, value["asset"], value["ndvi"], value["ndwi"], limitations)
            for period, value in (("before", metadata["before"]), ("after", metadata["after"]))
        ]


class DisabledRemoteAdapter:
    """Sentinel/Landsat/weather extension point; cannot run until configured."""
    def __init__(self, name: str): self.name = name
    def catalogue(self, watershed_id: str) -> list[ImageryCandidate]:
        raise RuntimeError(f"{self.name} is disabled. Configure approved provider credentials before enabling ingestion.")


def observed_change_summary(before: ImageryCandidate, after: ImageryCandidate) -> str:
    ndvi_change = (after.ndvi or 0) - (before.ndvi or 0)
    ndwi_change = (after.ndwi or 0) - (before.ndwi or 0)
    direction = "improved" if ndvi_change > 0 and ndwi_change > 0 else "declined" if ndvi_change < 0 and ndwi_change < 0 else "changed"
    return f"Observed NDVI changed by {ndvi_change:+.2f} and NDWI by {ndwi_change:+.2f}; indicators {direction}. This does not establish causality."
