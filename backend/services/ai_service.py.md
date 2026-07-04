# ai_service.py

## Source File

- `backend/services/ai_service.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It contains reusable backend business or integration logic.
- Provides the AI assistant integration layer, including production `.env.production` provider settings when `APP_ENV=production`, DB-configured encrypted provider selection, OpenAI-compatible provider calls, provider fallback by priority, tolerant JSON response parsing, token usage extraction, and deterministic local fallback responses.
- When a DB-configured provider has no stored key, `_call_configured_provider` falls back to that provider's `.env.production` key via `ai_provider_bootstrap.env_api_key_for`.
- `route_to_agent(message, agent_options, db)` is a lightweight LLM router used by `ai_agents.select_agent`: it iterates usable clients via `_iter_clients` (active DB providers by priority, then the env client), asks the model for `{"agent_key": ...}`, validates the key against the provided options, and returns `None` when no provider is configured or the model fails — so the caller degrades to keyword routing.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\services\<module>.py; run targeted backend tests when available
- `generate_vision_response(prompt, image_base64, mime_type, db)`: multimodal call through the same OpenAI-SDK clients (OpenAI directly; Anthropic via its OpenAI-compatible /v1 base_url). NO local fallback - raises RuntimeError when no vision provider is reachable so callers surface an honest 503 (grade OCR consumes this). Requires a vision-capable default_model.
- Provider-type allowlist includes "genspark"; the requires-base_url set is now {claude, manus, genspark} (anthropic/gemini carry OpenAI-compatible defaults from the bootstrap).
- Env loading imports ENV_FILE/ENV_PRODUCTION_FILE from backend.database (root-anchored) instead of CWD-relative load_dotenv calls.
