# ai_credit_sync.py

## Source File

- `backend/services/ai_credit_sync.py`

## Purpose

- Fetches provider AI credit balances from official APIs where that is possible, and reports honestly where it is not.
- `balance_api_supported(type)` marks which provider types expose a usable balance (currently only OpenRouter via `GET /credits`). `sync_provider_credits(provider)` returns a status dict (`synced | unsupported | no_key | auth_error | error`); `apply_sync_result` persists a synced balance.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- OpenAI, Anthropic, Google Gemini, xAI (Grok) and Manus do not expose a remaining-credit balance via their standard API keys, so their figure stays a manually-entered value; this is an API limitation, not a bug.
- Provider keys are read from the encrypted DB record first; when absent, the provider's `.env.production` key is resolved through `ai_provider_bootstrap.env_api_key_for` (single source of truth for env key names/aliases). Keys are never logged or returned.
- Network/auth failures are caught and returned as a status, never raised to the caller of `sync_provider_credits`.

## Verification

- python -m py_compile backend\services\ai_credit_sync.py; python -m pytest backend/test_ai_credit_sync.py
