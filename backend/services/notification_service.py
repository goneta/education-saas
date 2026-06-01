import os
from typing import Optional, Tuple

import httpx

from .. import models, schemas


def _provider_endpoint(provider: models.NotificationProvider) -> Optional[str]:
    if provider.provider_name.startswith("http://") or provider.provider_name.startswith("https://"):
        return provider.provider_name
    env_name = f"NOTIFICATION_{provider.provider_name.upper().replace('-', '_')}_WEBHOOK_URL"
    return os.getenv(env_name)


def dispatch_notification(provider: Optional[models.NotificationProvider], payload: schemas.NotificationMessageCreate) -> Tuple[models.NotificationStatus, str]:
    if not provider or not provider.is_active:
        return models.NotificationStatus.QUEUED, "Queued: no active provider selected."

    endpoint = _provider_endpoint(provider)
    if not endpoint:
        return models.NotificationStatus.QUEUED, "Queued: provider webhook URL is not configured."

    headers = {"Content-Type": "application/json"}
    if provider.api_key_secret:
        headers["Authorization"] = f"Bearer {provider.api_key_secret}"

    body = {
        "channel": payload.channel.value if hasattr(payload.channel, "value") else str(payload.channel),
        "recipient": payload.recipient,
        "subject": payload.subject,
        "message": payload.message,
        "sender_id": provider.sender_id,
    }

    try:
        response = httpx.post(endpoint, json=body, headers=headers, timeout=15)
        if response.status_code >= 400:
            return models.NotificationStatus.FAILED, f"Provider error {response.status_code}: {response.text[:500]}"
        return models.NotificationStatus.SENT, f"Provider accepted message: {response.text[:500]}"
    except httpx.HTTPError as exc:
        return models.NotificationStatus.FAILED, f"Provider request failed: {exc}"
