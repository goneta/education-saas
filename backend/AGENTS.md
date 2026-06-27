# Purpose

- Own the FastAPI backend for TeducAI: API entrypoint, routers, SQLAlchemy models, schemas, auth, RBAC, audit, security, observability, services, PDFs, localization, and backend tests.

# Ownership

- `main.py`, `models.py`, `schemas.py`, `database.py`, `security*.py`, `auth.py`, `rbac.py`, `audit.py`, `tenancy.py`, `localization.py`, `pdf.py`, `observability.py`.
- `routers/`: FastAPI route modules.
- `services/`: backend service logic and provider integrations.
- `scripts/`: backend backup/restore utilities.
- `test_*.py`: backend tests.

# Local Contracts

- API changes must preserve tenant isolation, RBAC checks, audit logging for sensitive actions, and existing route behavior unless explicitly changed.
- Model changes that affect production schema require an Alembic migration under `alembic/versions`.
- Do not restore `Base.metadata.create_all()` as a substitute for production migrations.
- Secrets and provider keys must not be logged or returned in API responses.
- The system super administrator bootstrap must stay idempotent and shared between CLI and HTTP entrypoints.
- Use `backend.tenancy` helpers for school-scoped routes that support both global `SUPER_ADMIN` access and school-local users.
- Cash payments and AI credit movements must preserve payment method, validator, internal reference, wallet balances, paired transactions, and audit history.
- School profile edits, logo uploads, subscriptions, user administration, and RBAC changes must persist through audited tenant-scoped APIs; paid subscriptions remain pending until payment confirmation.
- User deletion is soft deletion so referenced academic, financial, and audit history remains intact.
- User profile photos are tenant-protected secure files; only the user or an authorized administrator may upload, read, replace, or delete them.
- Official PDFs must use the shared school document header so persisted identity, address, phone, email, registration number, and local logo stay consistent.
- Multi-school data uses organization, school, school-model assignment, and academic-year context; frontend identifiers are never authoritative without backend membership validation.
- A learner has one durable `StudentGlobalProfile`; school/year/model participation is represented by `StudentEnrollment`, and academic or financial records should carry `student_enrollment_id` when applicable.
- Closed or archived academic years are read-only at the backend. Historical writes require Super Admin access or a scoped, time-limited, audited `HistoricalDataEditGrant`.
- Cross-school transfers may expose approved historical academic data but must never expose another school's finance.
- The public marketing site is content-managed: `SiteContent` is a Super Admin-owned singleton with public read and Super Admin-only writes, and the site must keep rendering from code-level defaults when no content is saved.
- A teacher has one durable `TeacherProfile`; school/model engagement is represented by `TeacherAssignment`, so teacher visibility and access derive from active assignments (a teacher may teach at several schools at once), not solely from the primary `users.school_id`.

# Work Guidance

- Prefer service functions for reusable business rules and keep routers focused on request/response orchestration.
- Use `backend.services.super_admin.ensure_super_admin` for super-admin account creation or repair instead of duplicating bootstrap logic.
- `SUPER_ADMIN` must remain global with `school_id = None`; school-dependent creation must require an explicit school selection.
- Use structured SQLAlchemy queries and Pydantic schemas instead of ad hoc serialization.
- For financial, AI, file, auth, or tenant-sensitive changes, add or update targeted tests when feasible.

# Verification

- Targeted syntax check: `python -m py_compile backend\\models.py backend\\schemas.py backend\\main.py`.
- Before running tests, ensure the local SQLite database matches the migration head: `python -m alembic upgrade head`. Tests use the real app/database wiring (no isolated test DB), so a stale or missing local `education_saas.db` causes widespread, misleading failures (e.g. `no such column`) unrelated to the code under test.
- Backend tests: `python -m pytest backend`. Note `test_auth.py` requires a separately running live server on `localhost:8000` and is not a self-contained pytest case; the rest use `TestClient` directly against the app.
- Import smoke check: `python -c "import backend.main as m; print(m.app.title)"`.

# Child DOX Index

- `routers/AGENTS.md`: FastAPI route modules and API boundary behavior.
- `services/AGENTS.md`: reusable backend business logic and provider integrations.
- `scripts/AGENTS.md`: backend backup/restore scripts.

Root backend files and `test_*.py` remain owned by this document.
