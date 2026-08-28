from io import BytesIO

import piexif
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def image_bytes(with_gps: bool) -> bytes:
    image = Image.new("RGB", (24, 24), color="forestgreen")
    output = BytesIO()
    exif = {"0th": {piexif.ImageIFD.Orientation: 1}, "Exif": {piexif.ExifIFD.DateTimeOriginal: b"2026:08:28 09:30:00"}, "GPS": {}, "1st": {}, "thumbnail": None}
    if with_gps:
        exif["GPS"] = {piexif.GPSIFD.GPSLatitudeRef: b"N", piexif.GPSIFD.GPSLatitude: ((19, 1), (0, 1), (360, 100)), piexif.GPSIFD.GPSLongitudeRef: b"E", piexif.GPSIFD.GPSLongitude: ((73, 1), (0, 1), (480, 100))}
    image.save(output, "jpeg", exif=piexif.dump(exif))
    return output.getvalue()


def test_gps_tagged_image_returns_coordinates() -> None:
    response = client.post("/api/v1/field-evidence", files={"file": ("gps-demo.jpg", image_bytes(True), "image/jpeg")})
    assert response.status_code == 200
    assert response.json()["metadata"]["gps"] == {"latitude": 19.001, "longitude": 73.00133333333333}
    assert response.json()["metadata"]["captured_at"] == "2026-08-28T09:30:00"
    assert response.json()["metadata"]["orientation"] == 1
    assert response.json()["geoproof"]["verdict"] == "Needs Review"
    assert response.json()["visual_assessment"]["label"] == "Check Dam"
    assert response.json()["impact_assessment"]["score"] == 85


def test_all_approved_demo_classes_and_unknown_are_labelled_transparently() -> None:
    expected = {"approved-check-dam.jpg": "Check Dam", "approved-farm-pond.jpg": "Farm Pond", "approved-erosion.jpg": "Erosion", "approved-waterbody.jpg": "Waterbody", "unapproved.jpg": "Unknown / Needs Review"}
    for filename, label in expected.items():
        response = client.post("/api/v1/field-evidence", files={"file": (filename, image_bytes(True), "image/jpeg")})
        assessment = response.json()["visual_assessment"]
        assert response.status_code == 200
        assert assessment["label"] == label
        assert assessment["method"] == "controlled_demo_metadata"

    assert client.post("/api/v1/field-evidence", files={"file": ("unapproved.jpg", image_bytes(True), "image/jpeg")}).json()["visual_assessment"]["review_status"] == "Needs Review"
    assert client.post("/api/v1/field-evidence", files={"file": ("approved-check-dam.jpg", image_bytes(True), "image/jpeg")}).json()["visual_assessment"]["consistency"]["status"] == "Consistent"
    assert client.post("/api/v1/field-evidence", files={"file": ("approved-farm-pond.jpg", image_bytes(True), "image/jpeg")}).json()["visual_assessment"]["consistency"]["status"] == "Inconsistent"


def test_image_without_exif_requires_manual_review() -> None:
    response = client.post("/api/v1/field-evidence", files={"file": ("plain-demo.jpg", image_bytes(False), "image/jpeg")})
    assert response.status_code == 200
    assert response.json()["metadata"]["gps"] is None
    assert response.json()["review_message"] == "No GPS metadata found — manual review required."
    assert response.json()["geoproof"]["total_score"] == 0
    assert response.json()["visual_assessment"]["label"] == "Unknown / Needs Review"


def test_non_image_upload_is_rejected() -> None:
    response = client.post("/api/v1/field-evidence", files={"file": ("notes.txt", b"not an image", "text/plain")})
    assert response.status_code == 415
    assert response.json()["detail"]["code"] == "unsupported_file_type"
