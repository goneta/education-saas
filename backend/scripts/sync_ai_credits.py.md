# sync_ai_credits.py

## Source File

- `backend/scripts/sync_ai_credits.py`

## Purpose

- Scheduled (cron) job that refreshes AI provider credit balances from official APIs, reusing `ai_credit_sync`. Balance-capable providers (OpenRouter) are updated; others are reported as `unsupported` and keep their manual value.

## DOX Scope

- Nearest contract: `backend/scripts/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Run from system cron, e.g. `0 3 * * * cd /opt/teducai && APP_ENV=production python -m backend.scripts.sync_ai_credits >> /var/log/teducai/ai_sync.log 2>&1`.
- `run_sync(db)` is idempotent, commits on success, audits the run as `platform.ai_credits.cron_synced`, and is the unit-tested entry point. `main()` opens a session, prints a per-provider report, and returns a non-zero exit code on failure.
- No secrets are embedded; provider keys come from the encrypted DB rows or `.env.production` via `ai_credit_sync`.

## Verification

- python -m py_compile backend\scripts\sync_ai_credits.py; python -m pytest backend/test_sync_ai_credits_script.py
