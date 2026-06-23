# employment.py

## Source File

- `backend/services/employment.py`

## Purpose

- Provides reusable TeducAI Emploi business logic for sharecode generation, automatic student CV creation, academic-year CV snapshots, public CV privacy filtering, sector catalog, and sharecode rate limiting.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Sharecodes must remain unique and should not expose private data beyond student registration/global identifiers already intended for student references.
- Public payloads must be filtered through `DEFAULT_PRIVACY`.
- Academic snapshots imported at year closure are historical CV data and should be treated as locked display data.

## Verification

- `python -m py_compile backend\services\employment.py`
- Run targeted backend tests for sharecode, privacy filtering, and year-closure CV refresh when available.
