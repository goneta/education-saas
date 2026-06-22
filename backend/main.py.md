# main.py

## Source File

- `backend/main.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Creates the FastAPI app, middleware stack, health/readiness/metrics endpoints, and registers all routers including bootstrap and multi-school context.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
# Student lifecycle

The application registers the `/student-lifecycle` router for global student profiles, enrollments, transfers, academic locks, historical edit grants, and import/export.
