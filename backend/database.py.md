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
- Env loading: `.env` first; `.env.production` (override) when APP_ENV=production; NEW fallback — when APP_ENV is unset and only `.env.production` exists at the root (typical prod host without an exported APP_ENV), it is loaded as the env source so AI provider keys / DATABASE_URL work out of the box.
- Env files are ROOT-ANCHORED (PROJECT_ROOT/ENV_FILE/ENV_PRODUCTION_FILE from Path(__file__)): the previous CWD-relative load_dotenv made `uvicorn backend.main:app` resolve a different SECRET_KEY (401 on PM2-minted JWTs) and fall back to sqlite instead of the production DATABASE_URL when launched from another directory. Every launch mode now loads the same files.
