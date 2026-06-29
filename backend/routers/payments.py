"""Centralized Payment Service API — the single entry point every TeducAI module
uses to confirm and reconcile school-side payments (tuition, transport, exam,
canteen, …). No module implements its own payment confirmation.

Slice 0 of the Goal Forge plan. Complements the existing checkout flow
(`commerce.py`) and gateways (`payment_gateway.py`): those create `pending`
`SchoolPayment` rows; this router confirms them idempotently (via signed provider
webhooks or authorized manual reconciliation) and updates the owning business
module through `services/payment_service.py`.
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security
from ..services import payment_service

router = APIRouter(prefix="/payments", tags=["Payment Service"])

MANAGER_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.ACCOUNTANT,
    models.UserRole.CASHIER,
}


def _verify_signature(provider: str, provided: Optional[str]) -> None:
    """Verify a provider webhook. Uses the provider-specific secret if set, else
    a shared `SCHOOL_PAYMENT_WEBHOOK_SECRET`. When no secret is configured the
    check is skipped (dev), mirroring the existing platform webhook. Real
    provider signature schemes (e.g. Stripe HMAC over the raw body) plug in here.
    """
    secret = os.getenv(f"{provider.upper()}_WEBHOOK_SECRET") or os.getenv("SCHOOL_PAYMENT_WEBHOOK_SECRET")
    if secret and provided != secret:
        raise HTTPException(status_code=403, detail="Invalid webhook signature")


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


@router.get("/providers")
def list_providers(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    """Payment providers enabled for the caller's institution."""
    school_id = _school_id(current_user)
    return {
        "enabled": payment_service.enabled_providers(db, school_id),
        "supported": sorted(payment_service.SUPPORTED_PROVIDERS),
    }


@router.post("/webhook/{provider}")
def payment_webhook(
    provider: str,
    payload: schemas.SchoolPaymentWebhook,
    x_teducai_webhook_secret: Optional[str] = Header(default=None),
    db: Session = Depends(database.get_db),
):
    """Confirm a school payment from a provider callback. Idempotent: a duplicate
    delivery for an already-successful payment is a safe no-op (the invoice is not
    double-credited)."""
    if provider.lower() not in payment_service.SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    _verify_signature(provider, x_teducai_webhook_secret)
    payment = db.query(models.SchoolPayment).filter(models.SchoolPayment.reference == payload.reference).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment introuvable")
    applied = payment_service.apply_school_payment(
        db, payment, status=payload.status, provider_reference=payload.provider_reference
    )
    db.commit()
    return {"reference": payment.reference, "status": payment.status, "applied": applied}


@router.post("/{reference}/verify")
def manual_verify(
    reference: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    """Manual reconciliation: an authorized cashier/accountant confirms a payment
    (e.g. after checking the provider dashboard). Idempotent and tenant-scoped."""
    if current_user.role not in MANAGER_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")
    school_id = _school_id(current_user)
    payment = (
        db.query(models.SchoolPayment)
        .filter(models.SchoolPayment.reference == reference, models.SchoolPayment.school_id == school_id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment introuvable")
    applied = payment_service.apply_school_payment(db, payment, status="successful", current_user=current_user)
    db.commit()
    return {"reference": payment.reference, "status": payment.status, "applied": applied}


@router.get("/{reference}")
def payment_status(
    reference: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    school_id = _school_id(current_user)
    payment = (
        db.query(models.SchoolPayment)
        .filter(models.SchoolPayment.reference == reference, models.SchoolPayment.school_id == school_id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment introuvable")
    return {
        "reference": payment.reference,
        "status": payment.status,
        "amount": payment.amount,
        "currency": payment.currency,
        "provider": payment.provider,
        "provider_reference": payment.provider_reference,
        "invoice_id": payment.invoice_id,
    }
