"""Test isolation for the whole backend suite.

Audit finding (pre-production, section 6/7): there was no `conftest.py`, so the
26 test modules that drive the real app through `TestClient(app)` wrote into the
developer database (`./education_saas.db`, already 7.3 MB of accumulated test
rows). Three consequences, all of them production risks:

* **The suite was not deterministic.** Runs accumulated schools, users and
  unique registration numbers, so ordering and uniqueness collisions made
  `test_ai_agent_rbac` and `test_timetable_constraint_api` fail in a full run
  while passing in isolation. A launch gate you cannot trust is not a gate.
* **It got slower every run** — a single school registration had grown to ~14 s
  against the bloated file, and the full suite took 11.5 minutes.
* **Nothing prevented a test run from writing to a real database.** If
  `DATABASE_URL` happened to point at staging or production, `TestClient`
  traffic would have gone straight into it.

This module fixes all three by pointing the suite at a private SQLite file
created per test session, before `backend.database` is imported anywhere (a
`conftest.py` is imported ahead of the test modules that sit beside it), and by
refusing to run against a non-SQLite database. Tests that already build their
own in-memory engine are unaffected.
"""

from __future__ import annotations

import os
import pathlib
import tempfile

# --- Guard: never let a test run touch a real database -----------------------
_configured = os.environ.get("DATABASE_URL", "")
if _configured and not _configured.startswith("sqlite"):
    raise RuntimeError(
        "Refusing to run the test suite against a non-SQLite DATABASE_URL "
        f"({_configured.split('://')[0]}://...). Unset DATABASE_URL to use the "
        "per-session test database."
    )

# --- Per-session database, isolated from the developer's file ----------------
# One file per process id keeps parallel runs (pytest-xdist, CI matrices) apart.
_TEST_DB = pathlib.Path(tempfile.gettempdir()) / f"teducai_test_{os.getpid()}.db"
_TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"

# A deterministic secret so token signing does not depend on the developer's env.
os.environ.setdefault("SECRET_KEY", "test-only-secret-not-used-in-production")

import pytest  # noqa: E402  (import after the env is fixed)

from backend import database  # noqa: E402
from backend import models  # noqa: E402  (registers every table on the metadata)


def pytest_configure(config):  # noqa: D401 - pytest hook
    """Create the schema once, before the first test runs."""
    database.Base.metadata.create_all(bind=database.engine)


def pytest_unconfigure(config):  # noqa: D401 - pytest hook
    """Drop the per-session database file so runs never accumulate state."""
    try:
        database.engine.dispose()
    finally:
        _TEST_DB.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def test_database_path() -> pathlib.Path:
    """Exposed for tests that need to inspect the session database directly."""
    return _TEST_DB
