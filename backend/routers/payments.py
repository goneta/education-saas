"""Centralized Payment Service API — the single entry point every TeducAI module
uses to confirm and reconcile school-side payments (tuition, transport, exam,
canteen, …). No module implements its own payment confirmation.

Slice 0 of the Goal Forge plan. Complements the existing checkout flow
(`commerce.py`) and gateways (`payment_gateway.py`): those create `pending`
`SchoolPayment` rows; this router confirms them idempotently (via signed provider
webhooks or authorized manual reconciliation) and updates the owning business
module through `services/payment_service.py`.
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from .. import database, models, schemas, security
from ..services import payment_gateway, payment_service

logger = logging.getLogger("teducai.payments")

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


def _find_payment(db: Session, reference: str):
    """Resolve a reference to its owning row: school-side (SCH-…) or
    platform-side (TPL-/SUB-/… PlatformPayment). Returns (kind, payment)."""
    school_payment = db.query(models.SchoolPayment).filter(models.SchoolPayment.reference == reference).first()
    if school_payment:
        return "school", school_payment
    platform_payment = db.query(models.PlatformPayment).filter(models.PlatformPayment.reference == reference).first()
    if platform_payment:
        return "platform", platform_payment
    return None, None


def _apply_verified_status(db: Session, kind: str, payment, status: str,
                           provider_reference: Optional[str], payload: dict,
                           current_user: Optional[models.User] = None) -> bool:
    """Apply a gateway-VERIFIED status through the shared idempotent appliers,
    persisting the gateway payload for reconciliation."""
    if kind == "school":
        applied = payment_service.apply_school_payment(
            db, payment, status=status, provider_reference=provider_reference, current_user=current_user
        )
        payment.metadata_json = {**(payment.metadata_json or {}), "gateway_check": payload}
        return applied
    return payment_service.apply_platform_payment(
        db, payment, status=status, provider_reference=provider_reference,
        extra_metadata={"gateway_check": payload},
    )


@router.post("/cinetpay/notify")
async def cinetpay_notify(request: Request, x_token: Optional[str] = Header(default=None),
                          db: Session = Depends(database.get_db)):
    """CinetPay-native notification endpoint (set as `notify_url`).

    Security model:
    1. The `x-token` HMAC-SHA256 (CINETPAY_SECRET_KEY) is validated when
       configured — a forged notification is rejected with 403.
    2. The notification body is NEVER trusted for the status. The transaction
       is re-verified server-side against `/v2/payment/check` and only that
       verified status is applied — this defeats forgery AND replay: replaying
       an old notify simply re-checks the gateway and hits the idempotent
       no-op path.
    3. Status application goes through the shared idempotent Payment Service,
       so duplicate deliveries can never double-credit an invoice or wallet.
    Returns 503 when the gateway is unreachable so CinetPay retries later.
    """
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        raw = await request.json()
        form = raw if isinstance(raw, dict) else {}
    else:
        form = dict(await request.form())
    reference = str(form.get("cpm_trans_id") or form.get("transaction_id") or "").strip()
    if not reference:
        raise HTTPException(status_code=400, detail="Missing transaction reference")

    if not payment_gateway.verify_cinetpay_token(x_token, form):
        logger.warning("CinetPay notify rejected: bad x-token for %s", reference)
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    kind, payment = _find_payment(db, reference)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment introuvable")
    if getattr(payment, "provider", "") != "cinetpay":
        raise HTTPException(status_code=400, detail="Payment is not a CinetPay transaction")

    status, payload = payment_gateway.cinetpay_check_transaction(reference)
    if status == "unknown":
        # Do not guess: ask CinetPay to redeliver once the gateway answers.
        raise HTTPException(status_code=503, detail="Gateway verification unavailable, retry later")

    provider_reference = str(
        (payload.get("data") or {}).get("operator_id")
        or form.get("cpm_payid") or form.get("payment_token") or ""
    ) or None
    applied = _apply_verified_status(db, kind, payment, status, provider_reference, payload)
    db.commit()
    logger.info("CinetPay notify %s -> %s (applied=%s)", reference, status, applied)
    return {"reference": reference, "status": payment.status, "applied": applied}


@router.post("/{reference}/refresh")
def refresh_payment(reference: str,
                    current_user: models.User = Depends(security.get_current_user),
                    db: Session = Depends(database.get_db)):
    """Gateway-backed status refresh: re-verify the transaction with the
    provider and apply the VERIFIED result idempotently. Used by the checkout
    return page (polling), payers retrying, and cashiers reconciling — unlike
    `/verify`, this never blindly marks success."""
    kind, payment = _find_payment(db, reference)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment introuvable")
    is_manager = current_user.role in MANAGER_ROLES
    is_payer = getattr(payment, "payer_user_id", None) == current_user.id
    same_school = getattr(payment, "school_id", None) == current_user.school_id
    if not (is_payer or (is_manager and (same_school or current_user.role == models.UserRole.SUPER_ADMIN))):
        raise HTTPException(status_code=403, detail="Not authorized")
    if payment.provider != "cinetpay":
        raise HTTPException(status_code=400, detail="Refresh is only available for CinetPay payments")

    status, payload = payment_gateway.cinetpay_check_transaction(reference)
    if status == "unknown":
        raise HTTPException(status_code=503, detail="Gateway verification unavailable, retry later")
    applied = _apply_verified_status(db, kind, payment, status, None, payload, current_user=current_user)
    db.commit()
    return {"reference": reference, "status": payment.status, "applied": applied, "kind": kind}


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
