# JalDrishti AI MVP - final SIH demo checklist

## Pre-demo setup (5 minutes before)

- [ ] Open two Git Bash terminals in the repository.
- [ ] Backend: run `cd backend`, `source .venv/Scripts/activate`, then `uvicorn app.main:app --reload --port 8000`.
- [ ] Frontend: run `cd frontend`, then `npm run dev`.
- [ ] Open `http://localhost:5173` and click **Load Demo Scenario**.
- [ ] Confirm the dashboard shows GeoProof `100/100`, Impact Score `91/100`, Nala Check Dam, High Runoff Risk, and **Download Impact Report**.
- [ ] Open one generated report before presenting to confirm the browser permits downloads.
- [ ] Keep `docs/demo-script.md` open as presenter notes.

## During the demo

- [ ] State that all displayed pilot values and images are curated demo data.
- [ ] Explain the GeoProof factors; do not describe the score as certification.
- [ ] Show the classifier confidence and its human-review caveat.
- [ ] Move the satellite comparison slider and state its seasonal/rainfall limitations.
- [ ] Select High Runoff Risk and read the rule-based recommendation reasons.
- [ ] Download the one-page report and point out its data-source and limitation note.

## Backup steps

- **No internet:** continue with the local neutral basemap, local GeoJSON, demo evidence art, prepared satellite assets, and local PDF service. No live map tiles or satellite downloads are required.
- **Real image has no GPS:** show the manual-review message, then use **Load Demo Scenario** for the verified happy path.
- **Report, upload, or recommendation says local service unavailable:** confirm the backend terminal is running on port 8000; restart it with the pre-demo command.
- **Frontend does not load:** stop its process with `Ctrl+C`, run `npm install` from `frontend`, then run `npm run dev` again.

## Common evaluator questions

| Question | Concise answer |
| --- | --- |
| Is this a live satellite analysis? | No. The MVP uses prepared, clearly labelled pilot assets so the demo remains offline and reproducible. |
| Does GeoProof prove fraud or construction quality? | No. It is a transparent evidence-review score; field survey and engineering approval are still required. |
| Is the visual detector a production AI model? | No. It is a controlled, limited-scope demo classifier and explicitly asks for review on low confidence or unknown images. |
| Where is personal data stored? | Nowhere in the MVP. Upload inspection is in memory and the demo assets contain no personal data. |
| What happens after the MVP? | Connect approved field records and governed geospatial sources, preserve provenance, and validate decisions through surveys and engineering review. |
