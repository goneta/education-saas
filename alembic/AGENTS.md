# Purpose

- Own Alembic migration configuration and versioned database schema changes.

# Ownership

- `env.py`: migration environment setup.
- `versions/`: ordered Alembic revisions for production schema evolution.

# Local Contracts

- Migrations must be versioned, deterministic, and safe to apply in production order.
- `0001` is a frozen initial schema and must not dynamically create the current model schema.
- PostgreSQL enums are global objects; avoid duplicate enum creation by using existing-type patterns where needed.
- Every backend model/schema change that changes database structure must be represented by a migration.

# Work Guidance

- Keep revision IDs, `down_revision`, and upgrade/downgrade paths coherent.
- Prefer explicit table/column/index operations over broad runtime patches.

# Verification

- Heads check: `python -m alembic heads`.
- Current check: `python -m alembic current`.
- Upgrade check: `python -m alembic upgrade head` when it is safe to mutate the active local database.

# Child DOX Index

- `versions/AGENTS.md`: ordered Alembic migration revision files.

`env.py` remains owned by this document.
