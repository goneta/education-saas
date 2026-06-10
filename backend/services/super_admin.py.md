# super_admin.py

## Source File

- `backend/services/super_admin.py`

## Purpose

- Provides the idempotent backend bootstrap service for the TeducAI system super administrator.
- Creates or repairs the `kenguigocis` account, hashes the bootstrap password, resets the role assignment to `super_admin`, activates/verifies the system account, and ensures a large AI credit wallet.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Never return or log plaintext passwords.
- Keep this service idempotent so CLI and HTTP bootstrap paths produce the same account state.
- Changes to persistent user fields must be represented by Alembic migrations.

## Verification

- `python -m py_compile backend\services\super_admin.py`
