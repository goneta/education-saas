"""Outbound webhook delivery worker (audit OPS-02).

`extensibility.emit_event` has always queued deliveries, but nothing ever sent
them: rows piled up in `pending` while the "API & Integrations" page advertised
working integrations. This module is the missing sender.

Design constraints kept deliberately simple (no broker, no daemon):
- it is a **pull** runner (`dispatch_pending`) driven by cron, exactly like the
  other TeducAI automations — one more line in `teducai-cron.example`;
- every request is **signed** (HMAC-SHA256 of the raw body with the endpoint's
  secret, header `X-TeducAI-Signature`) so the receiver can authenticate it,
  the same doctrine we require from our own inbound webhooks;
- failures are **retried with exponential backoff** up to `max_attempts`, then
  marked `failed` with the reason kept in `last_error` — never silently dropped.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from .. import models

logger = logging.getLogger("teducai.webhook_dispatch")

REQUEST_TIMEOUT_SECONDS = 15


def _now() -> datetime:
    return datetime.now(timezone.utc)


def sign_payload(secret: Optional[str], body: bytes) -> Optional[str]:
    if not secret:
        return None
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _due(delivery: models.WebhookDelivery) -> bool:
    if delivery.status != "pending":
        return False
    if delivery.next_retry_at is None:
        return True
    due_at = delivery.next_retry_at
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)
    return due_at <= _now()


def deliver_one(db: Session, delivery: models.WebhookDelivery, *, client: Optional[httpx.Client] = None) -> str:
    """Send one delivery and record the outcome. Returns the resulting status."""
    endpoint = (
        db.query(models.WebhookEndpoint)
        .filter(models.WebhookEndpoint.id == delivery.endpoint_id)
        .first()
    )
    if not endpoint or not endpoint.is_active:
        delivery.status = "failed"
        delivery.last_error = "Endpoint supprimé ou désactivé"
        return delivery.status

    body = json.dumps(
        {"event": delivery.event_type, "school_id": delivery.school_id, "data": delivery.payload or {}},
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    headers = {"Content-Type": "application/json", "X-TeducAI-Event": delivery.event_type or ""}
    signature = sign_payload(endpoint.secret, body)
    if signature:
        headers["X-TeducAI-Signature"] = signature

    delivery.attempts = (delivery.attempts or 0) + 1
    try:
        sender = client or httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS)
        response = sender.post(endpoint.url, content=body, headers=headers)
        if client is None:
            sender.close()
        if 200 <= response.status_code < 300:
            delivery.status = "delivered"
            delivery.last_error = None
            delivery.next_retry_at = None
            return delivery.status
        reason = f"HTTP {response.status_code}"
    except Exception as exc:  # network error, DNS, TLS…
        reason = f"{exc.__class__.__name__}: {exc}"

    delivery.last_error = reason[:500]
    if delivery.attempts >= (delivery.max_attempts or 5):
        delivery.status = "failed"
        delivery.next_retry_at = None
    else:
        delivery.status = "pending"
        # Exponential backoff: 2, 4, 8, 16… minutes.
        delivery.next_retry_at = _now() + timedelta(minutes=2 ** delivery.attempts)
    logger.warning("Webhook delivery %s failed (%s), attempt %s", delivery.id, reason, delivery.attempts)
    return delivery.status


def dispatch_pending(db: Session, *, limit: int = 100, client: Optional[httpx.Client] = None) -> dict:
    """Send every due delivery. Safe to run from cron as often as needed."""
    candidates = (
        db.query(models.WebhookDelivery)
        .filter(models.WebhookDelivery.status == "pending")
        .order_by(models.WebhookDelivery.id.asc())
        .limit(min(max(limit, 1), 500))
        .all()
    )
    summary = {"considered": len(candidates), "delivered": 0, "retrying": 0, "failed": 0, "skipped": 0}
    for delivery in candidates:
        if not _due(delivery):
            summary["skipped"] += 1
            continue
        status = deliver_one(db, delivery, client=client)
        if status == "delivered":
            summary["delivered"] += 1
        elif status == "failed":
            summary["failed"] += 1
        else:
            summary["retrying"] += 1
    db.commit()
    return summary
