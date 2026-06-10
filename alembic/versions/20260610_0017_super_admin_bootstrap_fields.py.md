# 20260610_0017_super_admin_bootstrap_fields.py

## Source File

- `alembic/versions/20260610_0017_super_admin_bootstrap_fields.py`

## Purpose

- Ordered Alembic migration that adds system super-admin bootstrap fields to `users`.
- Adds nullable unique `username` plus non-null `is_verified` and `is_system_account` flags with safe defaults.

## DOX Scope

- Nearest contract: `alembic/versions/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Keep this migration deterministic and ordered after `20260610_0016`.
- Apply before running `python create_super_admin.py` or `python manage.py create_super_admin`.

## Verification

- `python -m alembic heads`
- `python -m alembic upgrade head` when it is safe to mutate the active database
