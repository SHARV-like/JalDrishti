# JalDrishti AI - 3-minute SIH demo script

## Before presenting

1. Start the local FastAPI service on port 8000 and the frontend on port 5173.
2. Open `http://localhost:5173` and click **Load Demo Scenario**.
3. Confirm the dashboard shows the local offline basemap label, a verified GeoProof result, an Impact Score, and the Nala Check Dam site panel.

## Exact presenter flow

### 0:00 - Set the problem

“JalDrishti AI turns intervention evidence into a transparent decision-support story: where a water intervention is, whether the field evidence is credible, its pilot impact signal, and what action should come next.”

### 0:20 - Load the ready pilot scenario

Click **Load Demo Scenario**.

“For a reliable competition demonstration, this loads a complete curated pilot scenario locally. No cloud services, live satellite downloads, personal data, or secrets are required.”

### 0:40 - Explain GeoProof

Point to the Field Evidence card.

“This local demo image has GPS and capture-time metadata. GeoProof explains its 100 out of 100 score factor by factor: it is inside the prepared watershed, near Nala Check Dam, and has valid GPS and capture time.”

### 1:05 - Show the map and site evidence

Point to the purple evidence marker, distance line, and Nala Check Dam panel.

“The map shows the watershed boundary, intervention inventory, the uploaded-evidence location, and the nearest intervention. Clicking any marker opens its timeline, evidence state, impact, and residual risk.”

### 1:30 - Show satellite impact

Move the before/after slider.

“These prepared pilot assets show a positive NDVI change of 0.18 and NDWI change of 0.09. We state clearly that these indicators are not proof of causality; seasons, rainfall, cloud cover, and crop cycles matter.”

### 1:55 - Explain residual risk and recommendation

Select **High Runoff Risk**.

“The red zone exposes its slope, runoff, vegetation, terrain/soil, and drainage inputs. The rule engine ranks three options and explains why Contour Trench is the recommended next action. Field survey and engineering approval remain mandatory.”

### 2:25 - Export the report

Click **Download Impact Report** in the Nala Check Dam site panel.

“This produces a one-page local PDF with the evidence, verification, satellite indicators, remaining risk, recommendation, data sources, and limitations.”

### 2:45 - Close

“JalDrishti AI makes each claim traceable, keeps demo assumptions visible, and gives decision-makers a clear starting point for field validation.”

## Backup steps

### Internet is unavailable

Continue normally. The map uses a local neutral basemap and local GeoJSON layers; field-evidence illustrations, satellite assets, scoring, recommendations, and report generation all use local project files. Do not depend on browser map tiles.

### Image metadata is unavailable

Use **Load Demo Scenario**. It restores the verified local pilot record. If demonstrating a real no-EXIF image, say: “No GPS metadata found - manual review required,” then explain that GeoProof visibly reduces the score rather than inventing certainty.

### Local API is not running

From `backend`, run `source .venv/Scripts/activate` then `uvicorn app.main:app --reload --port 8000`. The UI displays actionable local-service error messages for uploads, recommendations, and reports.
