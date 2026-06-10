# ai_credits.py

## Source File

- `backend/services/ai_credits.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It contains reusable backend business or integration logic.
- Owns AI credit accounting rules: wallet creation, balance checks, daily/monthly credit limit enforcement, token-to-credit conversion, usage logs, credit transactions, and successful platform payment application.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\services\<module>.py; run targeted backend tests when available
