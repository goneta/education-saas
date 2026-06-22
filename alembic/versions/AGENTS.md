# Purpose

- Own versioned Alembic migration files.

# Ownership

- All migration revision files under `alembic/versions/`.

# Local Contracts

- Each migration must have a stable `revision` and correct `down_revision`.
- Migrations must not depend on current SQLAlchemy metadata to define historical schema.
- Downgrades should be present and coherent for structural changes unless a task explicitly documents why downgrade is unsupported.

# Work Guidance

- Use explicit operations for tables, columns, constraints, indexes, seed data, and enum handling.
- For PostgreSQL enums, avoid duplicate `CREATE TYPE` failures by using existing-type-safe patterns where needed.
- Unique constraints containing nullable tenant columns require explicit PostgreSQL partial unique indexes for the global (`school_id IS NULL`) scope.
- Multi-context migrations must backfill existing schools and business records without replacing historical identifiers or relations.
- Student lifecycle migrations must preserve legacy student/profile IDs, create deterministic global identities, backfill current enrollments, and record migration counts and warnings.

# Verification

- `python -m alembic heads`
- `python -m alembic upgrade head` when it is safe to mutate the active local database.

# Child DOX Index

- No child AGENTS.md files yet.
