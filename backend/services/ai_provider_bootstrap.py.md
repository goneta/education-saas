# ai_provider_bootstrap.py

## Source File

- `backend/services/ai_provider_bootstrap.py`

## Purpose

- Auto-registers AI providers from `.env.production` (process env) so any provider whose key is present drives the chat and credit sync without manual UI entry.
- `bootstrap_providers_from_env(db)` creates/refreshes env-seeded rows (tagged `account_label="env"`); `env_api_key_for(type)` resolves a provider's env API key (with aliases).

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Idempotent: env-seeded rows are updated in place (no duplicates); UI-created providers (any other `account_label`) are never touched.
- Supported env keys: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`/`GOOGLE_API_KEY`, `XAI_API_KEY`/`GROK_API_KEY`, `ANTHROPIC_API_KEY`, `MANUS_API_KEY`, with optional `*_MODEL` and `*_BASE_URL`.
- OpenRouter/Gemini/xAI have OpenAI-compatible base URLs; Anthropic/Manus serve chat only when an OpenAI-compatible `*_BASE_URL` is supplied (otherwise the priority fallback skips them). Keys are stored encrypted, never logged.
- Invoked best-effort from the FastAPI startup hook in `main.py`.

## Verification

- python -m py_compile backend\services\ai_provider_bootstrap.py; python -m pytest backend/test_ai_provider_bootstrap.py
