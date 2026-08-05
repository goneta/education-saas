"""Shared-secret authentication for inbound provider webhooks — FAIL-CLOSED.

Audit SEC-01: the previous checks read `if secret and provided != secret: 403`.
When the environment variable was absent the condition was false and the
request was accepted **with no authentication at all** — on public endpoints
that credit AI wallets, activate subscriptions and settle student invoices.
Combined with SEC-02 (the secret was documented nowhere and unchecked by the
production audit script), an anonymous caller could grant themselves credits or
mark tuition paid.

The rule is now: in production a missing secret is a *server misconfiguration*,
never an open door. We answer 503 so the provider retries the delivery once the
secret is set — no money side-effect is applied in the meantime, mirroring the
CinetPay "fail toward retry, never toward guessing" doctrine.

Outside production the check still degrades to a no-op so local development and
the test suite keep working without secrets.
"""

import hmac
import logging
import os
from typing import Optional

from fastapi import HTTPException

from . import database

logger = logging.getLogger("teducai.webhook_auth")

UNCONFIGURED_DETAIL = "Webhook authentication is not configured on this server"


def resolve_secret(*env_names: str) -> Optional[str]:
    """First non-empty value among the given environment variable names."""
    for name in env_names:
        value = os.getenv(name)
        if value:
            return value
    return None


def verify_shared_secret(provided: Optional[str], *env_names: str, purpose: str) -> None:
    """Authenticate a webhook call against a configured shared secret.

    Raises 503 when no secret is configured in production (fail-closed), 403 on
    mismatch. Comparison is constant-time.
    """
    secret = resolve_secret(*env_names)
    if not secret:
        if database.is_production():
            logger.error(
                "Refusing %s webhook: none of %s is configured on this production host",
                purpose, ", ".join(env_names),
            )
            raise HTTPException(status_code=503, detail=UNCONFIGURED_DETAIL)
        return  # development / tests: no secret required
    if not provided or not hmac.compare_digest(secret, provided):
        logger.warning("Rejected %s webhook: invalid shared secret", purpose)
        raise HTTPException(status_code=403, detail="Invalid webhook signature")
