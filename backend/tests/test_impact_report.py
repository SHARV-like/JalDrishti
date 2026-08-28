from io import BytesIO

from pypdf import PdfReader

from app.services.impact_report import build_impact_report


def test_builds_a_single_page_pilot_impact_report():
    report = build_impact_report("demo-intervention-001")

    assert report is not None
    reader = PdfReader(BytesIO(report))
    assert len(reader.pages) == 1
    assert "Nala Check Dam" in reader.pages[0].extract_text()


def test_returns_none_for_unknown_pilot_site():
    assert build_impact_report("not-a-pilot-site") is None
