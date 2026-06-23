# database.py

## Source File

- `backend/database.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Loads `.env` by default and overlays `.env.production` only when `APP_ENV=production`, so production DATABASE_URL can drive backend/Alembic without breaking local tests.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
