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

## Impact and recommendation posture

Satellite, impact, risk, and recommendation values must record their input dates, source, method, limitations, ruleset version, and `data_status`. A demo or estimated result must never be displayed as observed evidence. Any future index uses documented normalised components and weights, and reports association rather than causal proof.
