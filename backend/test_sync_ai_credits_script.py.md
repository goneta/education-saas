# test_sync_ai_credits_script.py

## Purpose

- Verifies the cron `run_sync` updates a balance-capable provider (OpenRouter, mocked HTTP) and computes remaining = total − usage.
- Verifies unsupported providers (OpenAI) are reported and left unchanged, and disabled providers are excluded from the run.
- Verifies the run is audited as `platform.ai_credits.cron_synced`.

## Verification

- `python -m pytest backend/test_sync_ai_credits_script.py`
