"""Auto-detect AI providers from `.env.production` (or the process env).

When the Super Admin keeps provider keys in `.env.production`, this module turns
each present key into a usable `AIProvider` row so the chat and credit sync use
it directly — no manual UI entry required. Rows seeded from the environment are
tagged `account_label = "env"` and are kept in sync with the env on every boot;
providers created in the UI (any other label) are never touched.

OpenAI-compatible base URLs are used where the provider offers one (OpenRouter,
Gemini, xAI). Anthropic and Manus have no official OpenAI-compatible chat
endpoint, so they are seeded (visible/configurable) but only serve chat when an
OpenAI-compatible `*_BASE_URL` is supplied; otherwise the priority fallback
moves on to the next provider.
"""

import logging
import os
from typing import Optional

from sqlalchemy.orm import Session

from .. import crypto_utils, models

logger = logging.getLogger(__name__)

ENV_LABEL = "env"

# Order defines default priority (lower = tried first).
PROVIDER_SPECS = [
    {
        "type": "openai", "name": "OpenAI",
        "key_envs": ["OPENAI_API_KEY"],
        "base_url_env": "OPENAI_BASE_URL", "default_base_url": None,
        "model_env": "OPENAI_MODEL", "default_model": "gpt-4.1-mini",
    },
    {
        "type": "openrouter", "name": "OpenRouter",
        "key_envs": ["OPENROUTER_API_KEY"],
        "base_url_env": "OPENROUTER_BASE_URL", "default_base_url": "https://openrouter.ai/api/v1",
        "model_env": "OPENROUTER_MODEL", "default_model": "openrouter/auto",
    },
    {
        "type": "gemini", "name": "Google Gemini",
        "key_envs": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "base_url_env": "GEMINI_BASE_URL", "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model_env": "GEMINI_MODEL", "default_model": "gemini-2.0-flash",
    },
    {
        "type": "grok", "name": "xAI Grok",
        "key_envs": ["XAI_API_KEY", "GROK_API_KEY"],
        "base_url_env": "XAI_BASE_URL", "default_base_url": "https://api.x.ai/v1",
        "model_env": "XAI_MODEL", "default_model": "grok-2-latest",
    },
    {
        # Anthropic exposes an OpenAI-compatible endpoint at /v1, so the shared
        # OpenAI-SDK client (chat + vision) works out of the box with just
        # ANTHROPIC_API_KEY set.
        "type": "anthropic", "name": "Anthropic Claude",
        "key_envs": ["ANTHROPIC_API_KEY"],
        "base_url_env": "ANTHROPIC_BASE_URL", "default_base_url": "https://api.anthropic.com/v1/",
        "model_env": "ANTHROPIC_MODEL", "default_model": "claude-3-5-sonnet-latest",
    },
    {
        "type": "manus", "name": "Manus",
        "key_envs": ["MANUS_API_KEY"],
        "base_url_env": "MANUS_BASE_URL", "default_base_url": None,
        "model_env": "MANUS_MODEL", "default_model": None,
    },
]

_KEY_ENV_BY_TYPE = {spec["type"]: spec["key_envs"] for spec in PROVIDER_SPECS}


def env_api_key_for(provider_type: Optional[str]) -> Optional[str]:
    """Return the first configured env API key for a provider type, if any."""
    for env_name in _KEY_ENV_BY_TYPE.get((provider_type or "").lower(), []):
        value = os.getenv(env_name)
        if value:
            return value
    return None


def _first_env(names: list[str]) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def bootstrap_providers_from_env(db: Session) -> dict:
    """Create/refresh env-seeded providers from the current environment.

    Idempotent: env-seeded rows are updated in place; UI-created rows are left
    untouched. Returns counts for observability.
    """
    created = 0
    updated = 0
    for index, spec in enumerate(PROVIDER_SPECS):
        api_key = _first_env(spec["key_envs"])
        if not api_key:
            continue
        base_url = os.getenv(spec["base_url_env"]) or spec["default_base_url"]
        model = os.getenv(spec["model_env"]) or spec["default_model"]
        row = db.query(models.AIProvider).filter(
            models.AIProvider.provider_type == spec["type"],
            models.AIProvider.account_label == ENV_LABEL,
        ).first()
        if not row:
            db.add(models.AIProvider(
                name=spec["name"],
                provider_type=spec["type"],
                api_key_encrypted=crypto_utils.encrypt_secret(api_key),
                base_url=base_url,
                default_model=model,
                account_label=ENV_LABEL,
                available_credits=0,
                is_active=True,
                priority=10 + index,
            ))
            created += 1
        else:
            row.api_key_encrypted = crypto_utils.encrypt_secret(api_key)
            row.base_url = base_url
            row.default_model = model
            row.is_active = True
            updated += 1
    if created or updated:
        db.commit()
    logger.info("AI provider env bootstrap: created=%s updated=%s", created, updated)
    return {"created": created, "updated": updated}
