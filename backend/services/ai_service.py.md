# ai_service.py

## Source File

- `backend/services/ai_service.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It contains reusable backend business or integration logic.
- Provides the AI assistant integration layer, including production `.env.production` provider settings when `APP_ENV=production`, DB-configured encrypted provider selection, OpenAI-compatible provider calls, provider fallback by priority, tolerant JSON response parsing, token usage extraction, and deterministic local fallback responses.
- When a DB-configured provider has no stored key, `_call_configured_provider` falls back to that provider's `.env.production` key via `ai_provider_bootstrap.env_api_key_for`.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\services\<module>.py; run targeted backend tests when available
