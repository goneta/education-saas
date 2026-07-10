"""Centralized Payment Service — idempotent confirmation + per-institution
gateway configuration for school-side payments.

Slice 0 of the TeducAI Goal Forge plan. The checkout flow (`commerce.py`) and the
provider gateways (`payment_gateway.py`) already exist and create `pending`
`SchoolPayment` rows; the missing piece was a single, idempotent path that
*confirms* a payment and updates its owning business module (e.g. a
`StudentInvoice`). This module is that path, mirroring the existing platform
webhook in `ai_billing.py` so behaviour stays consistent and un-duplicated.

No module should re-implement payment confirmation: call `apply_school_payment`.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import audit, models
from .automation import record_notification

CASH = "cash"
# Providers the platform's gateways know how to talk to (see payment_gateway.py).
SUPPORTED_PROVIDERS = {"stripe", "cinetpay", "djamo", CASH}


def enabled_providers(db: Session, school_id: int) -> list[str]:
    """Providers an institution has switched on (active `SchoolPaymentAccount`
    rows), plus cash which authorized staff can always record."""
    accounts = (
        db.query(models.SchoolPaymentAccount)
        .filter(
            models.SchoolPaymentAccount.school_id == school_id,
            models.SchoolPaymentAccount.is_active == True,  # noqa: E712
        )
        .all()
    )
    providers = {(account.provider or "").lower() for account in accounts if account.provider}
    providers.add(CASH)
    return sorted(providers)


def is_provider_enabled(db: Session, school_id: int, provider: str) -> bool:
    return (provider or "").lower() in set(enabled_providers(db, school_id))


def apply_school_payment(
    db: Session,
    payment: models.SchoolPayment,
    *,
    status: str,
    provider_reference: Optional[str] = None,
    current_user: Optional[models.User] = None,
) -> bool:
    """Idempotently apply a payment status to a SchoolPayment.

    On the first transition to "successful" the side-effects run exactly once:
    the owning `StudentInvoice` balance is updated, an audit record is written and
    the payer is notified. A second call with the same successful status is a
    safe no-op (returns False) — this is what makes webhook delivery and manual
    reconciliation idempotent and prevents double-charging an invoice.

    Returns True only when this call newly confirmed the payment.
    """
    if provider_reference:
        payment.provider_reference = provider_reference

    normalized = (status or "").lower()
    if normalized != "successful":
        # Non-success statuses (failed/cancelled/pending) just record the state.
        payment.status = normalized or payment.status
        return False

    if payment.status == "successful":
        return False  # already applied — do not re-update the business module

    payment.status = "successful"

    if payment.invoice_id:
        invoice = (
            db.query(models.StudentInvoice)
            .filter(models.StudentInvoice.id == payment.invoice_id, models.StudentInvoice.school_id == payment.school_id)
            .first()
        )
        if invoice:
            invoice.amount_paid = (invoice.amount_paid or 0) + payment.amount
            invoice.remaining_balance = max((invoice.amount_due or 0) - invoice.amount_paid, 0)
            invoice.status = (
                models.StudentInvoiceStatus.PAID
                if invoice.remaining_balance <= 0
                else models.StudentInvoiceStatus.PARTIAL
            )

    audit.record_audit(
        db,
        action="school.payment.confirmed",
        current_user=current_user,
        entity_type="school_payment",
        entity_id=payment.reference,
        details={
            "amount": payment.amount,
            "currency": payment.currency,
            "provider": payment.provider,
            "invoice_id": payment.invoice_id,
        },
    )

    if payment.student_id:
        record_notification(
            db,
            event_type="finance.payment_confirmed",
            subject="Paiement confirmé",
            message=f"Paiement de {payment.amount} {payment.currency} confirmé ({payment.payment_type}).",
            school_id=payment.school_id,
            student_id=payment.student_id,
            source_type="school_payment",
            source_id=payment.id,
            current_user=current_user,
        )
    return True


def apply_platform_payment(
    db: Session,
    payment: models.PlatformPayment,
    *,
    status: str,
    provider_reference: Optional[str] = None,
    extra_metadata: Optional[dict] = None,
) -> bool:
    """Idempotently apply a status to a PlatformPayment (credits/subscription).

    Mirrors `apply_school_payment` for platform-side money: on the FIRST
    transition to "successful" the credit wallet is topped up (via
    `ai_credits.apply_platform_payment_success`, itself idempotent) or the
    subscription is activated. Duplicate deliveries are safe no-ops. This is
    the single confirmation path shared by the legacy platform webhook and the
    CinetPay notify endpoint — no module re-implements it.
    """
    from . import ai_credits  # local import to avoid a service-layer cycle

    if provider_reference:
        payment.provider_reference = provider_reference
    if extra_metadata:
        payment.metadata_json = {**(payment.metadata_json or {}), **extra_metadata}

    normalized = (status or "").lower()
    if normalized != "successful":
        if payment.status != "successful":  # never downgrade a confirmed payment
            payment.status = normalized or payment.status
        return False
    if payment.status == "successful":
        return False

    payment.status = "successful"
    if payment.payment_type == "ai_credit_purchase":
        ai_credits.apply_platform_payment_success(db, payment)
    elif payment.payment_type == "subscription" and payment.school_id:
        subscription = (
            db.query(models.SchoolSubscription)
            .filter(
                models.SchoolSubscription.payment_reference == payment.reference,
                models.SchoolSubscription.school_id == payment.school_id,
            )
            .order_by(models.SchoolSubscription.id.desc())
            .first()
        )
        if subscription:
            now = datetime.now(timezone.utc)
            renewal = now + (timedelta(days=365) if subscription.billing_cycle == "yearly" else timedelta(days=30))
            subscription.status = "active"
            subscription.started_at = now
            subscription.next_renewal_at = renewal
            subscription.expires_at = renewal
            school = db.query(models.School).filter(models.School.id == payment.school_id).first()
            if school:
                school.subscription_plan = subscription.plan
                school.subscription_status = "active"
                school.current_billing_period_end = renewal

    audit.record_audit(
        db,
        action="platform.payment.confirmed",
        entity_type="platform_payment",
        entity_id=payment.reference,
        details={"amount": payment.amount, "currency": payment.currency,
                 "provider": payment.provider, "payment_type": payment.payment_type},
    )
    return True
