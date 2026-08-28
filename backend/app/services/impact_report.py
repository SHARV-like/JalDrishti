from __future__ import annotations

import io
import json
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PAGE_WIDTH, PAGE_HEIGHT = 595, 842  # A4 portrait


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _label(value: str) -> str:
    return value.replace("_", " ").title()


def _text(pdf: canvas.Canvas, text: str, x: float, y: float, size: float = 9, color=colors.HexColor("#19383a"), font: str = "Helvetica") -> None:
    pdf.setFont(font, size)
    pdf.setFillColor(color)
    pdf.drawString(x, y, text)


def _wrapped(pdf: canvas.Canvas, text: str, x: float, y: float, width: float, size: float = 8.4, leading: float = 11, color=colors.HexColor("#466467")) -> float:
    words, line = text.split(), ""
    pdf.setFont("Helvetica", size)
    pdf.setFillColor(color)
    for word in words:
        candidate = f"{line} {word}".strip()
        if stringWidth(candidate, "Helvetica", size) > width and line:
            pdf.drawString(x, y, line)
            y -= leading
            line = word
        else:
            line = candidate
    if line:
        pdf.drawString(x, y, line)
        y -= leading
    return y


def _box(pdf: canvas.Canvas, x: float, y: float, width: float, height: float, fill="#f3f8f7", stroke="#d6e5e3") -> None:
    pdf.setFillColor(colors.HexColor(fill))
    pdf.setStrokeColor(colors.HexColor(stroke))
    pdf.roundRect(x, y, width, height, 8, fill=1, stroke=1)


def _image(pdf: canvas.Canvas, path: Path, x: float, y: float, width: float, height: float) -> None:
    if path.suffix.lower() == ".svg":
        drawing = svg2rlg(str(path))
        if drawing:
            scale = min(width / drawing.width, height / drawing.height)
            drawing.scale(scale, scale)
            renderPDF.draw(drawing, pdf, x + (width - drawing.width * scale) / 2, y + (height - drawing.height * scale) / 2)
            return
    pdf.drawImage(ImageReader(str(path)), x, y, width, height, preserveAspectRatio=True, anchor="c", mask="auto")


def build_impact_report(site_id: str) -> bytes | None:
    interventions = _load_json(PROJECT_ROOT / "data" / "geo" / "interventions.geojson")["features"]
    feature = next((item for item in interventions if item["properties"]["id"] == site_id), None)
    details = _load_json(PROJECT_ROOT / "data" / "geo" / "intervention-site-details.json")["sites"].get(site_id)
    satellite = _load_json(PROJECT_ROOT / "data" / "satellite" / "metadata.json")
    if not feature or not details:
        return None

    props, coordinates = feature["properties"], feature["geometry"]["coordinates"]
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream, pagesize=(PAGE_WIDTH, PAGE_HEIGHT), pageCompression=1)
    pdf.setTitle(f"JalDrishti AI Impact Report - {props['name']}")

    pdf.setFillColor(colors.HexColor("#073235"))
    pdf.rect(0, PAGE_HEIGHT - 82, PAGE_WIDTH, 82, fill=1, stroke=0)
    _text(pdf, "JalDrishti AI", 34, PAGE_HEIGHT - 41, 25, colors.white, "Helvetica-Bold")
    _text(pdf, "INTERVENTION IMPACT REPORT", 35, PAGE_HEIGHT - 59, 8, colors.HexColor("#8de7ed"), "Helvetica-Bold")
    _text(pdf, f"Report date: {date.today().strftime('%d %B %Y')}  |  CURATED PILOT / DEMO DATA", 314, PAGE_HEIGHT - 51, 7.4, colors.HexColor("#d2ece9"), "Helvetica-Bold")

    _text(pdf, "Illustrative Demo Watershed", 34, 730, 10, colors.HexColor("#0e7490"), "Helvetica-Bold")
    _text(pdf, "38.6 ha  |  Offline prepared MVP assets  |  Not for field decisions", 34, 716, 8)
    _text(pdf, props["name"], 34, 682, 19, colors.HexColor("#102f31"), "Helvetica-Bold")
    _text(pdf, f"{_label(props['intervention_type'])}  |  Status: {props['status']}  |  Completion: {details['completion_date']}", 34, 665, 8.6)

    _box(pdf, 34, 530, 245, 117)
    _text(pdf, "FIELD EVIDENCE", 46, 630, 7.5, colors.HexColor("#0e7490"), "Helvetica-Bold")
    evidence = details["latest_evidence"]
    if evidence:
        _image(pdf, PROJECT_ROOT / "data" / evidence["image"].lstrip("/"), 46, 548, 150, 70)
        _wrapped(pdf, evidence["caption"], 205, 598, 62, 7.1, 9)
    else:
        pdf.setFillColor(colors.HexColor("#fff7e8")); pdf.roundRect(46, 550, 221, 66, 6, fill=1, stroke=0)
        _text(pdf, "Evidence incomplete", 57, 588, 10, colors.HexColor("#a16207"), "Helvetica-Bold")
        _wrapped(pdf, "No field image or verified GPS record is available for this pilot site.", 57, 572, 190, 7.5, 10)

    _box(pdf, 293, 530, 268, 117)
    _text(pdf, "GEOLOCATION & VERIFICATION", 305, 630, 7.5, colors.HexColor("#0e7490"), "Helvetica-Bold")
    _text(pdf, f"GPS: {coordinates[1]:.4f}, {coordinates[0]:.4f}", 305, 608, 9, font="Helvetica-Bold")
    score = details["geoproof"]["score"]
    _text(pdf, f"GeoProof: {'Pending' if score is None else str(score) + '/100'}", 305, 586, 15, colors.HexColor("#0e7490"), "Helvetica-Bold")
    _text(pdf, f"Status: {details['geoproof']['status']}", 305, 570, 8.5)
    _text(pdf, f"Remaining risk: {details['remaining_risk']}", 305, 550, 8.2)

    _text(pdf, "SATELLITE BEFORE / AFTER", 34, 503, 10, colors.HexColor("#0e7490"), "Helvetica-Bold")
    _box(pdf, 34, 353, 527, 137)
    before, after = satellite["before"], satellite["after"]
    _image(pdf, PROJECT_ROOT / "data" / before["asset"].lstrip("/"), 46, 378, 192, 90)
    _image(pdf, PROJECT_ROOT / "data" / after["asset"].lstrip("/"), 251, 378, 192, 90)
    _text(pdf, f"Before - {before['date']}", 46, 364, 7.5, font="Helvetica-Bold")
    _text(pdf, f"After - {after['date']}", 251, 364, 7.5, font="Helvetica-Bold")
    _text(pdf, f"NDVI: {before['ndvi']:.2f} to {after['ndvi']:.2f}  (+{after['ndvi'] - before['ndvi']:.2f})", 456, 437, 8.4, colors.HexColor("#087f5b"), "Helvetica-Bold")
    _text(pdf, f"NDWI: {before['ndwi']:.2f} to {after['ndwi']:.2f}  (+{after['ndwi'] - before['ndwi']:.2f})", 456, 416, 8.4, colors.HexColor("#087f5b"), "Helvetica-Bold")
    _wrapped(pdf, "Prepared illustrative pilot comparison; offline demo assets.", 456, 392, 92, 7.2, 9)

    _box(pdf, 34, 238, 245, 98, fill="#eaf8f4", stroke="#b7e3d3")
    _text(pdf, "OVERALL IMPACT SCORE", 46, 316, 7.5, colors.HexColor("#087f5b"), "Helvetica-Bold")
    impact = details["impact_score"]
    _text(pdf, "Pending" if impact is None else f"{impact}/100", 46, 280, 26, colors.HexColor("#087f5b"), "Helvetica-Bold")
    _wrapped(pdf, "Pilot impact indicator combines available GeoProof, vegetation, water response, and completion status.", 130, 300, 135, 7.4, 10)

    _box(pdf, 293, 238, 268, 98, fill="#f5f1ff", stroke="#ddd1ff")
    recommendation = details["recommendation"]
    _text(pdf, "RECOMMENDED NEXT ACTION", 305, 316, 7.5, colors.HexColor("#6d28d9"), "Helvetica-Bold")
    _text(pdf, f"{recommendation['action']} - {recommendation['score']}/100", 305, 295, 13, colors.HexColor("#5b21b6"), "Helvetica-Bold")
    _wrapped(pdf, " ".join(recommendation["reasons"]), 305, 278, 240, 7.5, 10)

    pdf.setStrokeColor(colors.HexColor("#d6e5e3")); pdf.line(34, 210, 561, 210)
    _text(pdf, "DATA SOURCES & LIMITATIONS", 34, 193, 8, colors.HexColor("#0e7490"), "Helvetica-Bold")
    _wrapped(pdf, "Sources: JalDrishti MVP curated pilot site data; local illustrative field-evidence art; prepared illustrative satellite assets. All values are demo data, not observed operational evidence.", 34, 178, 527, 7.3, 9.5)
    _wrapped(pdf, "Limitation: satellite-index changes can be influenced by season, rainfall, cloud cover, and crop cycles. Final intervention selection requires field survey and engineering approval.", 34, 145, 527, 7.3, 9.5, colors.HexColor("#8a5908"))
    _text(pdf, "JalDrishti AI MVP - transparent decision support", 34, 38, 7, colors.HexColor("#71918b"))
    _text(pdf, "Page 1 of 1", 507, 38, 7, colors.HexColor("#71918b"))
    pdf.showPage(); pdf.save()
    return stream.getvalue()
