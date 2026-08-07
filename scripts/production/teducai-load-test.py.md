# teducai-load-test.py
## Source File
- `scripts/production/teducai-load-test.py`
## Purpose
- Go criterion "test de charge": simulates a school-year-start peak — N
  concurrent authenticated clients hammering the screens everyone opens at once
  (dashboard, students, classes, timetable, attendance, assessments, active
  context). Reports throughput, error rate, p50/p95/p99/max and a per-screen p95
  ranking, then exits non-zero when the p95 budget is exceeded or any request
  failed (usable as a Go/No-Go gate).
## Local Contracts
- **READ-ONLY**: only GET endpoints are called, nothing is written.
- Must run against the REAL environment (PostgreSQL + production host + reverse
  proxy). Running it on a dev box (SQLite, single uvicorn process) measures the
  laptop, not the platform, and would give a falsely reassuring result.
- Configuration by environment: `TEDUCAI_URL`, `TEDUCAI_USERS`
  ("email:password,email:password"). Refuses to start without them.
## Verification
- `python scripts/production/teducai-load-test.py --help` and the missing-env
  guard both verified locally; the measurement itself is a production task.
