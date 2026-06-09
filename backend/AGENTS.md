# Purpose

- Own the FastAPI backend for TeducAI: API entrypoint, routers, SQLAlchemy models, schemas, auth, RBAC, audit, security, observability, services, PDFs, localization, and backend tests.

# Ownership

- `main.py`, `models.py`, `schemas.py`, `database.py`, `security*.py`, `auth.py`, `rbac.py`, `audit.py`, `localization.py`, `pdf.py`, `observability.py`.
- `routers/`: FastAPI route modules.
- `services/`: backend service logic and provider integrations.
- `scripts/`: backend backup/restore utilities.
- `test_*.py`: backend tests.

# Local Contracts

- API changes must preserve tenant isolation, RBAC checks, audit logging for sensitive actions, and existing route behavior unless explicitly changed.
- Model changes that affect production schema require an Alembic migration under `alembic/versions`.
- Do not restore `Base.metadata.create_all()` as a substitute for production migrations.
- Secrets and provider keys must not be logged or returned in API responses.

# Work Guidance

- Prefer service functions for reusable business rules and keep routers focused on request/response orchestration.
- Use structured SQLAlchemy queries and Pydantic schemas instead of ad hoc serialization.
- For financial, AI, file, auth, or tenant-sensitive changes, add or update targeted tests when feasible.

# Verification

- Targeted syntax check: `python -m py_compile backend\\models.py backend\\schemas.py backend\\main.py`.
- Backend tests: `python -m pytest backend`.
- Import smoke check: `python -c "import backend.main as m; print(m.app.title)"`.

# Child DOX Index

- `routers/AGENTS.md`: FastAPI route modules and API boundary behavior.
- `services/AGENTS.md`: reusable backend business logic and provider integrations.
- `scripts/AGENTS.md`: backend backup/restore scripts.

Root backend files and `test_*.py` remain owned by this document.
