# 20260622_0022_multi_school_model_context.py

## Purpose

- Adds organizations, the global school-model catalog, school/model assignments, persistent user context, model-scoped business columns, system-default markers, and contextual audit fields.
- Migrates every existing school into a default organization and derives its initial active model assignment from `schools.school_type`.

## Safety

- Existing identifiers and relations are preserved.
- New context columns remain nullable during the compatibility transition.
- Seed and backfill operations are idempotent.
- Upgrade and downgrade paths use explicit Alembic operations.

## Verification

- `python -m alembic upgrade head`
- `python -m alembic heads`
