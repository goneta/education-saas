# test_api_surface_smoke.py
## Source File
- `backend/test_api_surface_smoke.py`
## Purpose
- Anti-500 net over the WHOLE API surface — the campaign against silently
  swallowed errors. Enumerates every registered GET route without path
  parameters (213 today) and asserts none answers 500 on a coherent empty
  database. Tolerated: 422 (validation did its job), 404 (empty DB), 400/403
  (context or rights), 503 (external dependency honestly refused). Only 500 or
  an unhandled exception fails.
- Found on its first run: `/employment/public-profiles` (500 — the SEC-07 access
  log wrote a StudentCVAccessLog row without the NOT NULL `student_cv_id`, so
  the PUBLIC /emploi page was broken) and
  `/enterprise/direction-dashboard/advanced` (500 — ambiguous SQLAlchemy 2.0
  join with four selected entities).
## Local Contracts
- Exclusions are explicit and justified in `SKIP_EXACT` / `SKIP_PREFIXES` —
  never silent. `test_the_scan_actually_covers_the_api` fails if the enumeration
  itself breaks (guard on the guard).
- The session is rolled back after each request: one endpoint leaving a failed
  transaction used to poison every later test (135 failures for ONE real bug).
## Verification
- `python -m pytest backend/test_api_surface_smoke.py` (213 green).
