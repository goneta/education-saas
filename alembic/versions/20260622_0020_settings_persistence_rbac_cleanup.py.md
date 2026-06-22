# 20260622_0020_settings_persistence_rbac_cleanup.py

## Purpose

- Adds persistent school subscription records and soft-deletion timestamps for users.
- Cleans duplicate global RBAC rows and adds PostgreSQL partial unique indexes for global roles, permissions, and assignments whose `school_id` is `NULL`.

## Verification

- `python -m alembic heads`
- Apply against a PostgreSQL staging database with `python -m alembic upgrade head`.
