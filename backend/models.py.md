# models.py

## Source File

- `backend/models.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Defines the SQLAlchemy data model, including user system-account fields, AI provider configuration, AI wallets with daily/monthly limits, credit transactions, AI usage logs, platform payments, and school payment accounts.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
