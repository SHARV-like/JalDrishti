from datetime import datetime
from io import BytesIO
from typing import Any

from PIL import ExifTags, Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


def _decimal_coordinate(values: Any, reference: Any) -> float | None:
    """Convert EXIF DMS data to a decimal coordinate without guessing absent data."""
    if not values or not reference:
        return None

    def as_float(value: Any) -> float:
        return float(value[0]) / float(value[1]) if isinstance(value, tuple) else float(value)

    try:
        degrees, minutes, seconds = (as_float(value) for value in values)
        result = degrees + minutes / 60 + seconds / 3600
        ref = reference.decode() if isinstance(reference, bytes) else str(reference)
        return -result if ref.upper() in {"S", "W"} else result
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def extract_image_metadata(content: bytes) -> dict[str, Any]:
    """Extract a deliberately small, safe subset of image EXIF metadata."""
    try:
        image = Image.open(BytesIO(content))
        image.verify()
        image = Image.open(BytesIO(content))
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc

    exif = image.getexif()
    gps = exif.get_ifd(34853) if exif else {}
    camera = exif.get_ifd(34665) if exif else {}
    latitude = _decimal_coordinate(gps.get(2), gps.get(1))
    longitude = _decimal_coordinate(gps.get(4), gps.get(3))
    capture_timestamp = camera.get(36867) or exif.get(306)
    orientation = exif.get(274)

    parsed_timestamp = None
    if capture_timestamp:
        try:
            parsed_timestamp = datetime.strptime(str(capture_timestamp), "%Y:%m:%d %H:%M:%S").isoformat()
        except ValueError:
            parsed_timestamp = str(capture_timestamp)

    return {
        "gps": {"latitude": latitude, "longitude": longitude} if latitude is not None and longitude is not None else None,
        "captured_at": parsed_timestamp,
        "orientation": int(orientation) if orientation else None,
        "image_format": image.format,
    }
