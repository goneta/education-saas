# 20260610_0016_ai_provider_limits.py

## Source File

- `alembic/versions/20260610_0016_ai_provider_limits.py`

## Purpose

- Alembic migration that adds AI wallet daily/monthly credit limit columns and seeds the default AI provider catalog for Super Admin configuration.

## DOX Scope

- Nearest contract: `alembic/versions/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Applies after `20260609_0015`.
- Provider API keys are not seeded; they must be configured encrypted through the platform API.
- Downgrade removes the seeded provider catalog entries for the added provider types and drops the limit columns.

## Verification

- `python -m alembic heads`
- `python -m alembic upgrade head` when it is safe to mutate the active local database.
