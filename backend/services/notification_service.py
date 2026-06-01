import os
from typing import Optional, Tuple

import httpx

from .. import crypto_utils, models, schemas


def _provider_endpoint(provider: models.NotificationProvider) -> Optional[str]:
    if provider.provider_name.startswith("http://") or provider.provider_name.startswith("https://"):
        return provider.provider_name
    env_name = f"NOTIFICATION_{provider.provider_name.upper().replace('-', '_')}_WEBHOOK_URL"
    return os.getenv(env_name)


def _json(response: httpx.Response) -> str:
    return response.text[:500]


def _post(endpoint: str, body: dict, headers: dict) -> Tuple[models.NotificationStatus, str]:
    response = httpx.post(endpoint, json=body, headers=headers, timeout=15)
    if response.status_code >= 400:
        return models.NotificationStatus.FAILED, f"Provider error {response.status_code}: {_json(response)}"
    return models.NotificationStatus.SENT, f"Provider accepted message: {_json(response)}"


def _dispatch_twilio(provider: models.NotificationProvider, payload: schemas.NotificationMessageCreate) -> Tuple[models.NotificationStatus, str]:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = crypto_utils.decrypt_secret(provider.api_key_secret) or os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = provider.sender_id or os.getenv("TWILIO_FROM", "")
    if not account_sid or not token or not from_number:
        return models.NotificationStatus.QUEUED, "Queued: Twilio credentials are not configured."
    endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    response = httpx.post(endpoint, data={"From": from_number, "To": payload.recipient, "Body": payload.message}, auth=(account_sid, token), timeout=15)
    if response.status_code >= 400:
        return models.NotificationStatus.FAILED, f"Twilio error {response.status_code}: {_json(response)}"
    return models.NotificationStatus.SENT, f"Twilio accepted message: {_json(response)}"


def _dispatch_orange(provider: models.NotificationProvider, payload: schemas.NotificationMessageCreate) -> Tuple[models.NotificationStatus, str]:
    endpoint = os.getenv("ORANGE_SMS_URL") or _provider_endpoint(provider)
    token = crypto_utils.decrypt_secret(provider.api_key_secret) or os.getenv("ORANGE_SMS_TOKEN", "")
    sender = provider.sender_id or os.getenv("ORANGE_SMS_SENDER", "")
    if not endpoint or not token or not sender:
        return models.NotificationStatus.QUEUED, "Queued: Orange SMS credentials are not configured."
    return _post(endpoint, {"outboundSMSMessageRequest": {"address": payload.recipient, "senderAddress": sender, "outboundSMSTextMessage": {"message": payload.message}}}, {"Authorization": f"Bearer {token}", "Content-Type": "application/json"})


def _dispatch_whatsapp(provider: models.NotificationProvider, payload: schemas.NotificationMessageCreate) -> Tuple[models.NotificationStatus, str]:
    phone_number_id = provider.sender_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    token = crypto_utils.decrypt_secret(provider.api_key_secret) or os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    if not phone_number_id or not token:
        return models.NotificationStatus.QUEUED, "Queued: WhatsApp Business credentials are not configured."
    endpoint = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    body = {"messaging_product": "whatsapp", "to": payload.recipient, "type": "text", "text": {"body": payload.message}}
    return _post(endpoint, body, {"Authorization": f"Bearer {token}", "Content-Type": "application/json"})


def _dispatch_sendgrid(provider: models.NotificationProvider, payload: schemas.NotificationMessageCreate) -> Tuple[models.NotificationStatus, str]:
    token = crypto_utils.decrypt_secret(provider.api_key_secret) or os.getenv("SENDGRID_API_KEY", "")
    sender = provider.sender_id or os.getenv("SENDGRID_FROM_EMAIL", "")
    if not token or not sender:
        return models.NotificationStatus.QUEUED, "Queued: SendGrid credentials are not configured."
    body = {
        "personalizations": [{"to": [{"email": payload.recipient}]}],
        "from": {"email": sender},
        "subject": payload.subject or "Notification",
        "content": [{"type": "text/plain", "value": payload.message}],
    }
    return _post("https://api.sendgrid.com/v3/mail/send", body, {"Authorization": f"Bearer {token}", "Content-Type": "application/json"})


def _dispatch_mailgun(provider: models.NotificationProvider, payload: schemas.NotificationMessageCreate) -> Tuple[models.NotificationStatus, str]:
    domain = os.getenv("MAILGUN_DOMAIN", "")
    token = crypto_utils.decrypt_secret(provider.api_key_secret) or os.getenv("MAILGUN_API_KEY", "")
    sender = provider.sender_id or os.getenv("MAILGUN_FROM_EMAIL", "")
    if not domain or not token or not sender:
        return models.NotificationStatus.QUEUED, "Queued: Mailgun credentials are not configured."
    endpoint = f"https://api.mailgun.net/v3/{domain}/messages"
    response = httpx.post(endpoint, data={"from": sender, "to": payload.recipient, "subject": payload.subject or "Notification", "text": payload.message}, auth=("api", token), timeout=15)
    if response.status_code >= 400:
        return models.NotificationStatus.FAILED, f"Mailgun error {response.status_code}: {_json(response)}"
    return models.NotificationStatus.SENT, f"Mailgun accepted message: {_json(response)}"


def dispatch_notification(provider: Optional[models.NotificationProvider], payload: schemas.NotificationMessageCreate) -> Tuple[models.NotificationStatus, str]:
    if not provider or not provider.is_active:
        return models.NotificationStatus.QUEUED, "Queued: no active provider selected."

    provider_name = provider.provider_name.lower().replace("_", "-")
    try:
        if provider_name == "twilio":
            return _dispatch_twilio(provider, payload)
        if provider_name == "orange":
            return _dispatch_orange(provider, payload)
        if provider_name in {"whatsapp", "whatsapp-business"}:
            return _dispatch_whatsapp(provider, payload)
        if provider_name == "sendgrid":
            return _dispatch_sendgrid(provider, payload)
        if provider_name == "mailgun":
            return _dispatch_mailgun(provider, payload)
    except httpx.HTTPError as exc:
        return models.NotificationStatus.FAILED, f"Provider request failed: {exc}"

    endpoint = _provider_endpoint(provider)
    if not endpoint:
        return models.NotificationStatus.QUEUED, "Queued: provider webhook URL is not configured."

    headers = {"Content-Type": "application/json"}
    secret = crypto_utils.decrypt_secret(provider.api_key_secret)
    if secret:
        headers["Authorization"] = f"Bearer {secret}"

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
