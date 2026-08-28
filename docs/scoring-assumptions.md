# MVP scoring assumptions

## GeoProof v0.1

This transparent pilot score is a review aid, not a fraud finding or certified audit.

| Evidence component | Points |
| --- | ---: |
| Valid GPS metadata | 25 |
| Coordinate within the selected watershed | 25 |
| Within the configured intervention buffer | 20 |
| Capture time is available and plausible | 10 |
| Image/context evidence supports the claim | 20 |

Scores of 80–100 are labelled `verified`, 50–79 `needs_review`, and below 50 `not_verified`. Missing information earns no points and should be visible to the user.

## Residual-risk recommendation v0.1

The three pilot risk zones use curated `demo` inputs for slope, runoff proxy, vegetation condition, terrain/soil proxy, and drainage distance. Contour Trench, Farm Pond, and Check Dam scores are deterministic 0–100 suitability rules; the UI displays each input and option score. They are decision support only: final intervention selection requires a field survey and engineering approval.

## Impact and recommendation posture

Satellite, impact, risk, and recommendation values must record their input dates, source, method, limitations, ruleset version, and `data_status`. A demo or estimated result must never be displayed as observed evidence. Any future index uses documented normalised components and weights, and reports association rather than causal proof.

## Intervention site details and timeline v0.1

The site panel reads the curated `data/geo/intervention-site-details.json` pilot dataset. Dates, completion states, GPS coordinates, GeoProof scores, impact scores, remaining-risk labels, and evidence-timeline events are illustrative demo records, not operational site records. The local SVG images are explicitly labelled illustrative demo field evidence. An incomplete site displays an empty state; it must not be treated as verified until a field image with valid evidence is reviewed.
