# 20260607_0012_document_sharing.py

## Source File

- `alembic/versions/20260607_0012_document_sharing.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It is an ordered Alembic migration revision.

## DOX Scope

- Nearest contract: `alembic/versions/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- The upgrade path is intentionally idempotent for columns, indexes, the approval foreign key, and `document_shares` because legacy/local databases may already contain part of this schema before Alembic reaches revision `20260607_0012`.

## Verification

- python -m alembic heads; python -m alembic upgrade head when safe for the active database
