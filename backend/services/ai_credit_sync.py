"""Fetch provider credit balances from official APIs where it is possible.

Reality of provider APIs (see the audit report):
- OpenRouter exposes a usable balance via `GET /credits` (total_credits / total_usage).
- OpenAI, Anthropic, Google Gemini, xAI (Grok) and Manus do NOT expose a
  remaining-credit balance through their standard API keys, so their figure
  stays a manually-entered value maintained by the Super Admin.

Provider API keys are stored encrypted in the database (entered in the Super
Admin UI). As a bridge to `.env.production`-style configuration, when a provider
has no stored key this module falls back to a conventional environment variable.
"""

import logging
import os
from datetime import datetime
from typing import Optional

import httpx

from .. import crypto_utils, models

logger = logging.getLogger(__name__)

# Conventional env var per provider type, used only when no DB key is stored.
ENV_KEY_BY_TYPE = {
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "grok": "XAI_API_KEY",
    "xai": "XAI_API_KEY",
    "manus": "MANUS_API_KEY",
}

# Provider types whose public API returns a usable remaining-balance figure.
BALANCE_API_SUPPORTED = {"openrouter"}


def balance_api_supported(provider_type: Optional[str]) -> bool:
    return (provider_type or "").lower() in BALANCE_API_SUPPORTED


def resolve_api_key(provider: models.AIProvider) -> Optional[str]:
    if provider.api_key_encrypted:
        key = crypto_utils.decrypt_secret(provider.api_key_encrypted)
        if key:
            return key
    env_var = ENV_KEY_BY_TYPE.get((provider.provider_type or "").lower())
    return os.getenv(env_var) if env_var else None


def sync_provider_credits(provider: models.AIProvider) -> dict:
    """Return a sync result dict without mutating the provider.

    status is one of: synced | unsupported | no_key | auth_error | error.
    On `synced`, `available_credits` holds the fetched remaining balance.
    """
    ptype = (provider.provider_type or "").lower()
    if not balance_api_supported(ptype):
        return {
            "provider_id": provider.id,
            "name": provider.name,
            "status": "unsupported",
            "detail": "Ce fournisseur n'expose pas le solde de crédits via son API.",
        }
    key = resolve_api_key(provider)
    if not key:
        return {"provider_id": provider.id, "name": provider.name, "status": "no_key", "detail": "Aucune clé API configurée."}
    try:
        base = (provider.base_url or "https://openrouter.ai/api/v1").rstrip("/")
        response = httpx.get(f"{base}/credits", headers={"Authorization": f"Bearer {key}"}, timeout=15)
        response.raise_for_status()
        data = response.json().get("data", {}) or {}
        total = float(data.get("total_credits", 0) or 0)
        used = float(data.get("total_usage", 0) or 0)
        remaining = max(0, int(round(total - used)))
        return {
            "provider_id": provider.id,
            "name": provider.name,
            "status": "synced",
            "available_credits": remaining,
        }
    except httpx.HTTPStatusError as exc:
        status = "auth_error" if exc.response.status_code in (401, 403) else "error"
        logger.warning("AI credit sync HTTP error for provider %s: %s", provider.id, exc)
        return {"provider_id": provider.id, "name": provider.name, "status": status, "detail": str(exc)}
    except Exception as exc:  # pragma: no cover - network/parse failure path
        logger.warning("AI credit sync failed for provider %s: %s", provider.id, exc)
        return {"provider_id": provider.id, "name": provider.name, "status": "error", "detail": str(exc)}


def apply_sync_result(provider: models.AIProvider, result: dict) -> None:
    """Persist a successful sync onto the provider row."""
    if result.get("status") == "synced":
        provider.available_credits = int(result["available_credits"])
        provider.credits_last_synced_at = datetime.utcnow()
