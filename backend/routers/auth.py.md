# auth.py

## Source File

- `backend/routers/auth.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.
- Owns registration, login, MFA, and `/auth/me`; login accepts either email or username while keeping password verification and account lockout protections.
- School registration initializes an organization and initial model assignment without replacing existing academic data.
- `/auth/me` returns account-type metadata and a recommended dashboard path so the frontend can redirect recruiters, external students, school users, and super admins without guessing from UI state.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Existing recruiter profiles remain authoritative for recruiter routing even when an older account has a legacy primary role.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
