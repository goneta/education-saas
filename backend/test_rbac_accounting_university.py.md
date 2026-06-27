# test_rbac_accounting_university.py

## Source File

- `backend/test_rbac_accounting_university.py`

## Purpose

- Automated test source file.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- `test_fee_with_timezone_aware_due_date_does_not_crash` guards against a regression where a fee created with a timezone-aware ISO `due_date` (e.g. ending in `Z`, as produced by the frontend) crashed `automate_fee_change` with a naive/aware datetime comparison error.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
