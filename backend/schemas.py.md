# schemas.py

## Source File

- `backend/schemas.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Exposes API schemas for schools, users, AI billing, and other modules, including username and system-account flags in user responses.
- Defines Pydantic API contracts for school settings, cash fee payments, AI providers, wallets, targeted credit packs, manual cash/free credit validation, school allocations, platform payments, and school payments.
- AI credit purchase contracts carry target context, provider, optional Mobile Money network, redirect URLs, manual-validation notes, checkout URL, and provider status.
- Defines persistent subscription-change/response contracts and exposes managed-user phone/deletion state.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
