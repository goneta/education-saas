# test_system.py

## Source File

- `backend/test_system.py`

## Purpose

- Automated test source file.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant

## Coverage

- Verifies persistent school profile updates and localization defaults.
- Verifies Free activation and paid subscription pending-payment persistence.
- Verifies tenant-scoped user editing, multi-role assignment, soft deletion, and unique role catalog output.
