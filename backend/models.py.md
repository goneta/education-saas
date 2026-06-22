# models.py

## Source File

- `backend/models.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Defines the SQLAlchemy data model, including traceable cash fee payments, AI billing, persistent school subscriptions, soft-deleted users, RBAC, and school payment accounts.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- User records persist an optional protected `profile_photo_url`; school records do not own user profile photos.
- Organizations own schools; schools activate global school models through assignment rows.
- Core academic, finance, AI usage, preference, and audit records carry assignment-level context while seeded references expose `is_system_default`.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
