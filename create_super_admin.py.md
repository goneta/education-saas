# create_super_admin.py

## Source File

- `create_super_admin.py`

## Purpose

- Root CLI helper that bootstraps or repairs the TeducAI system super administrator account.
- It calls `backend.services.super_admin.ensure_super_admin`, hashes the configured password, assigns `super_admin`, activates the system account, and ensures the AI wallet has bootstrap credits.

## DOX Scope

- Nearest contract: root `AGENTS.md`
- Keep this documentation understandable together with root AGENTS.md.

## Maintenance Notes

- Do not print or store plaintext passwords.
- The default bootstrap password can be overridden with `TEDUCAI_SUPER_ADMIN_PASSWORD`.
- Run after Alembic migrations have added the required user columns.

## Verification

- `python -m py_compile create_super_admin.py`
- Operational command: `python create_super_admin.py`
