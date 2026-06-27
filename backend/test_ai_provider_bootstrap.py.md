# test_ai_provider_bootstrap.py

## Purpose

- Verifies env keys are auto-registered as encrypted, active providers with the right base URLs and `account_label="env"`.
- Verifies the bootstrap is idempotent (no duplicates) and refreshes the key on env-seeded rows.
- Verifies UI-created providers (other labels) are never modified by the bootstrap.
- Verifies `env_api_key_for` honours provider aliases (e.g. GROK_API_KEY for grok).

## Verification

- `python -m pytest backend/test_ai_provider_bootstrap.py`
