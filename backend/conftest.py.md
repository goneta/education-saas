# conftest.py
## Source File
- `backend/conftest.py`
## Purpose
- Test isolation for the whole backend suite (audit passe 3, P3-B). Points the
  suite at a private SQLite file per session (one per PID → parallel-safe),
  created before `backend.database` is imported, schema built at
  `pytest_configure`, file removed at `pytest_unconfigure`.
## Local Contracts
- **Refuses to run** when `DATABASE_URL` is not SQLite — a test run can never
  write into staging/production.
- Before this existed, the 26 `TestClient(app)` modules wrote into the developer
  database (7.3 MB accumulated): the suite was non-deterministic (3 phantom
  failures), slowed to 11 min 32 s, and nothing stopped it hitting a real DB.
- Tests that build their own in-memory engine (69 modules) are unaffected.
## Verification
- `python -m pytest backend` → 617 passed, 0 failed (was 3 failed / 607).
