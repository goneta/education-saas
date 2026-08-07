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

import uuid as _uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import audit, models
from . import money
from .automation import record_notification

CASH = "cash"
# Providers the platform's gateways know how to talk to (see payment_gateway.py).
SUPPORTED_PROVIDERS = {"stripe", "cinetpay", "djamo", CASH}

# User-facing payment methods. The UI displays THESE (operator brands), never
# the gateway's name — CinetPay stays an invisible implementation detail.
MOBILE_MONEY_METHODS = [
    {"key": "orange_money", "label": "Orange Money", "provider": "cinetpay"},
    {"key": "mtn_money", "label": "MTN Mobile Money", "provider": "cinetpay"},
    {"key": "moov_money", "label": "Moov Money", "provider": "cinetpay"},
    {"key": "wave", "label": "Wave", "provider": "cinetpay"},
]
_NETWORK_LABELS = {m["key"]: m["label"] for m in MOBILE_MONEY_METHODS}
_PROVIDER_LABELS = {
    "cinetpay": "Mobile Money",
    "stripe": "Carte bancaire",
    "djamo": "Djamo",
    CASH: "Espèces",
    "free": "Gratuit",
}


def user_facing_method(provider: Optional[str], network: Optional[str] = None) -> str:
    """The label shown to users and printed on receipts: the operator brand
    (Orange Money, MTN Mobile Money, Moov Money, Wave) when known, otherwise a
    neutral family name — never the gateway's name."""
    if network and network in _NETWORK_LABELS:
        return _NETWORK_LABELS[network]
    return _PROVIDER_LABELS.get((provider or "").lower(), provider or "—")


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
            # MONEY-02: amounts are FLOAT, so a fully paid invoice could keep a
            # 1e-16 residue, stay PARTIAL forever and block the pupil's
            # certificate. Normalize on write, compare with a tolerance.
            invoice.amount_paid = money.normalize((invoice.amount_paid or 0) + payment.amount)
            invoice.remaining_balance = money.remaining(invoice.amount_due, invoice.amount_paid)
            invoice.status = (
                models.StudentInvoiceStatus.PAID
                if money.is_settled(invoice.remaining_balance)
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
    generate_school_payment_receipt(db, payment, current_user=current_user)
    return True


def generate_school_payment_receipt(
    db: Session, payment: models.SchoolPayment, *, current_user: Optional[models.User] = None
) -> Optional[str]:
    """Automatic receipt for a CONFIRMED school payment. Idempotent per payment
    (one GeneratedDocument keyed on source_type/source_id), registered in the
    universal DocumentRegistry so the receipt is QR-verifiable at /verify/{uuid}.
    Returns the receipt reference (existing one on replay)."""
    from . import document_registry  # local import: registry also imports models

    existing = (
        db.query(models.GeneratedDocument)
        .filter(models.GeneratedDocument.source_type == "school_payment",
                models.GeneratedDocument.source_id == payment.id)
        .first()
    )
    if existing:
        return existing.reference

    school = db.query(models.School).filter(models.School.id == payment.school_id).first()
    if not school:
        return None
    payer = db.query(models.User).filter(models.User.id == payment.payer_user_id).first() if payment.payer_user_id else None
    student = (
        db.query(models.StudentProfile).filter(models.StudentProfile.id == payment.student_id).first()
        if payment.student_id else None
    )
    student_name = student.user.full_name if student and student.user else None
    issued_to = student_name or (payer.full_name if payer else None)
    network = (payment.metadata_json or {}).get("mobile_money_network")
    method = user_facing_method(payment.provider, network)
    reference = f"REC-{_uuid.uuid4().hex[:10].upper()}"
    payload = {
        "reference": reference,
        "doc_type": "receipt",
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "school": {"name": school.name, "address": school.address, "phone": school.phone,
                   "email": school.email, "logo_url": school.logo_url},
        "payer": {"full_name": payer.full_name if payer else None},
        "student": {"full_name": student_name,
                    "registration_number": student.registration_number if student else None},
        "payment": {
            "payment_reference": payment.reference,
            "payment_type": payment.payment_type,
            "amount": payment.amount,
            "currency": payment.currency,
            "method": method,
            "provider_reference": payment.provider_reference,
            "invoice_id": payment.invoice_id,
        },
    }
    db.add(models.GeneratedDocument(
        document_type=models.GeneratedDocumentType.RECEIPT,
        title="Reçu de paiement",
        reference=reference,
        source_type="school_payment",
        source_id=payment.id,
        student_id=payment.student_id,
        school_id=payment.school_id,
        content=payload,
        generated_by_id=current_user.id if current_user else payment.payer_user_id,
    ))
    registry = document_registry.register(
        db,
        document_type="receipt",
        school_id=payment.school_id,
        title="Reçu de paiement",
        reference=reference,
        issued_to_name=issued_to,
        issued_to_id=payment.payer_user_id,
        payload={
            "School": school.name,
            "Receipt Number": reference,
            "Payment Reference": payment.reference,
            "Amount": f"{payment.amount} {payment.currency}",
            "Method": method,
            "Date": document_registry.now_iso(),
        },
        source_type="school_payment",
        source_id=payment.id,
        issued_by=current_user,
    )
    payment.metadata_json = {
        **(payment.metadata_json or {}),
        "receipt_reference": reference,
        "receipt_verify_uuid": registry.uuid,
    }
    return reference


def refund_school_payment(
    db: Session,
    payment: models.SchoolPayment,
    *,
    current_user: models.User,
    reason: Optional[str] = None,
) -> bool:
    """Idempotently refund a CONFIRMED school payment: reverse the invoice
    balance, mark the payment refunded, revoke its receipt in the registry,
    audit and notify. The money movement itself happens at the provider
    (CinetPay merchant panel / cash drawer) — this records the verified
    reversal in the school's books; it never calls the gateway.

    Returns True when this call performed the refund; False when the payment
    was already refunded. Raises ValueError when the payment was never
    successful (nothing to refund)."""
    if payment.status == "refunded":
        return False
    if payment.status != "successful":
        raise ValueError("Only a successful payment can be refunded")

    payment.status = "refunded"

    if payment.invoice_id:
        invoice = (
            db.query(models.StudentInvoice)
            .filter(models.StudentInvoice.id == payment.invoice_id,
                    models.StudentInvoice.school_id == payment.school_id)
            .first()
        )
        if invoice:
            invoice.amount_paid = max(money.normalize((invoice.amount_paid or 0) - payment.amount), 0.0)
            invoice.remaining_balance = money.remaining(invoice.amount_due, invoice.amount_paid)
            invoice.status = (
                models.StudentInvoiceStatus.PAID if money.is_settled(invoice.remaining_balance)
                else models.StudentInvoiceStatus.PARTIAL if money.is_outstanding(invoice.amount_paid)
                else models.StudentInvoiceStatus.UNPAID
            )

    receipt_uuid = (payment.metadata_json or {}).get("receipt_verify_uuid")
    if receipt_uuid:
        from . import document_registry

        document_registry.revoke(db, receipt_uuid, current_user)

    audit.record_audit(
        db,
        action="school.payment.refunded",
        current_user=current_user,
        entity_type="school_payment",
        entity_id=payment.reference,
        details={"amount": payment.amount, "currency": payment.currency,
                 "provider": payment.provider, "invoice_id": payment.invoice_id,
                 "reason": reason},
    )
    if payment.student_id:
        record_notification(
            db,
            event_type="finance.payment_refunded",
            subject="Paiement remboursé",
            message=f"Le paiement de {payment.amount} {payment.currency} ({payment.payment_type}) a été remboursé.",
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
