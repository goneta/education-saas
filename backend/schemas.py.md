# schemas.py

## Source File

- `backend/schemas.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Defines Pydantic API contracts for school settings, AI providers, AI wallets, credit packs, usage logs, credit adjustments, platform payments, and school payments.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
