"""Platform Extensibility — outbound webhooks + tenant API keys (Slice 7,
Loop 10 gaps).

`emit_event` records a `WebhookDelivery` (status=pending, with retry bookkeeping)
for every active endpoint subscribed to the event — any module can call it to
publish a platform event. The actual HTTP sender/retry worker is a runtime
component (documented NOT READY); this slice owns the data model, subscription
matching and retry scheduling. API keys are stored hashed; the plaintext is
returned only once.
"""

import hashlib
import secrets as secretslib
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(prefix="/extensibility", tags=["Platform Extensibility"])

ADMIN_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _ensure_admin(current_user: models.User) -> None:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")


def emit_event(db: Session, school_id: int, event_type: str, payload: dict) -> int:
    """Queue a delivery for every active endpoint in the school subscribed to
    `event_type` (an endpoint with no `event_types` receives all). Returns the
    number of deliveries queued. Commit is the caller's responsibility."""
    endpoints = db.query(models.WebhookEndpoint).filter(
        models.WebhookEndpoint.school_id == school_id,
        models.WebhookEndpoint.is_active == True,  # noqa: E712
    ).all()
    queued = 0
    for endpoint in endpoints:
        subscribed = not endpoint.event_types or event_type in endpoint.event_types
        if not subscribed:
            continue
        db.add(models.WebhookDelivery(
            endpoint_id=endpoint.id,
            school_id=school_id,
            event_type=event_type,
            payload=payload,
            status="pending",
            next_retry_at=datetime.now(timezone.utc),
        ))
        queued += 1
    return queued


# --------------------------------------------------------------------------- #
# Webhook endpoints
# --------------------------------------------------------------------------- #
@router.get("/webhooks", response_model=List[schemas.WebhookEndpointResponse])
def list_webhooks(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    return db.query(models.WebhookEndpoint).filter(models.WebhookEndpoint.school_id == _school_id(current_user)).order_by(models.WebhookEndpoint.id.desc()).all()


@router.post("/webhooks", response_model=schemas.WebhookEndpointResponse)
def create_webhook(payload: schemas.WebhookEndpointCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    row = models.WebhookEndpoint(**payload.model_dump(), school_id=_school_id(current_user))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/webhooks/{endpoint_id}")
def delete_webhook(endpoint_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    row = db.query(models.WebhookEndpoint).filter(models.WebhookEndpoint.id == endpoint_id, models.WebhookEndpoint.school_id == _school_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Endpoint introuvable")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


@router.post("/deliveries/{delivery_id}/retry")
def retry_delivery(delivery_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Re-queue a failed delivery (manual retry; the automatic retry worker uses
    the same attempts/next_retry_at bookkeeping)."""
    _ensure_admin(current_user)
    row = db.query(models.WebhookDelivery).filter(models.WebhookDelivery.id == delivery_id, models.WebhookDelivery.school_id == _school_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Livraison introuvable")
    if row.attempts >= row.max_attempts:
        raise HTTPException(status_code=409, detail="Nombre maximal de tentatives atteint")
    row.status = "pending"
    row.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=2 ** row.attempts)
    db.commit()
    return {"id": row.id, "status": row.status, "attempts": row.attempts, "next_retry_at": row.next_retry_at}


# --------------------------------------------------------------------------- #
# API keys
# --------------------------------------------------------------------------- #
@router.get("/api-keys", response_model=List[schemas.ApiKeyResponse])
def list_api_keys(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    return db.query(models.ApiKey).filter(models.ApiKey.school_id == _school_id(current_user)).order_by(models.ApiKey.id.desc()).all()


@router.post("/api-keys", response_model=schemas.ApiKeyCreated)
def create_api_key(payload: schemas.ApiKeyCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Mint a key; only the hash is stored. The plaintext is returned ONCE."""
    _ensure_admin(current_user)
    raw = f"tk_{secretslib.token_urlsafe(32)}"
    row = models.ApiKey(
        school_id=_school_id(current_user),
        name=payload.name,
        prefix=raw[:10],
        key_hash=hashlib.sha256(raw.encode()).hexdigest(),
        created_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id, "school_id": row.school_id, "name": row.name, "prefix": row.prefix,
        "is_active": row.is_active, "created_at": row.created_at, "api_key": raw,
    }


@router.delete("/api-keys/{key_id}")
def revoke_api_key(key_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    row = db.query(models.ApiKey).filter(models.ApiKey.id == key_id, models.ApiKey.school_id == _school_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Clé introuvable")
    row.is_active = False
    db.commit()
    return {"status": "revoked"}
