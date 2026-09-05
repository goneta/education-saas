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
            "network": network,
            "provider_reference": payment.provider_reference,
        },
    }
    
    # Create GeneratedDocument entry for the receipt
    doc = models.GeneratedDocument(
        document_type=models.GeneratedDocumentType.RECEIPT,
        title=f"Reçu {reference}",
        reference=reference,
        source_type="school_payment",
        source_id=payment.id,
        student_id=payment.student_id,
        school_id=payment.school_id,
        content=payload,
        generated_by_id=current_user.id if current_user else None,
    )
    db.add(doc)
    db.flush()
    
    # Register in DocumentRegistry for QR verification
    doc_reg = document_registry.register(
        db,
        document_type="receipt",
        payload=payload,
        source_type="school_payment",
        source_id=payment.id,
    )
    
    # Link the receipt reference to the payment metadata
    payment.metadata_json = payment.metadata_json or {}
    payment.metadata_json["receipt_reference"] = doc.reference
    payment.metadata_json["receipt_verify_uuid"] = doc_reg.uuid
    
    return doc.reference


def refund_school_payment(
    db: Session,
    payment: models.SchoolPayment,
    *,
    reason: str,
    current_user: Optional[models.User] = None,
) -> bool:
    """Refund a CONFIRMED school payment. Idempotent: returns True if refund was applied, 
    False if already refunded or not confirmed. Updates payment.status to 'refunded' on success."""
    if payment.status != "successful":
        return False

    # Check if already refunded
    if payment.metadata_json and payment.metadata_json.get("refunded"):
        return False

    # Update payment metadata
    payment.metadata_json = payment.metadata_json or {}
    payment.metadata_json["refunded"] = True
    payment.metadata_json["refund_reason"] = reason
    payment.metadata_json["refunded_at"] = datetime.now(timezone.utc).isoformat()
    payment.metadata_json["refunded_by"] = current_user.id if current_user else None

    # Update invoice balance
    if payment.invoice_id:
        invoice = (
            db.query(models.StudentInvoice)
            .filter(models.StudentInvoice.id == payment.invoice_id, models.StudentInvoice.school_id == payment.school_id)
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

    # Revoke receipt
    from . import document_registry
    receipt = (
        db.query(models.GeneratedDocument)
        .filter(models.GeneratedDocument.source_type == "school_payment",
                models.GeneratedDocument.source_id == payment.id)
        .first()
    )
    if receipt:
        # Find the associated DocumentRegistry entry to get the UUID
        doc_reg = (
            db.query(models.DocumentRegistry)
            .filter(models.DocumentRegistry.source_type == "school_payment",
                    models.DocumentRegistry.source_id == payment.id)
            .first()
        )
        if doc_reg:
            document_registry.revoke(db, doc_reg.uuid, current_user)

    # Update payment status to refunded
    payment.status = "refunded"

    audit.record_audit(
        db,
        action="school.payment.refunded",
        current_user=current_user,
        entity_type="school_payment",
        entity_id=payment.reference,
        details={
            "amount": payment.amount,
            "currency": payment.currency,
            "reason": reason,
            "invoice_id": payment.invoice_id,
        },
    )

    if payment.student_id:
        record_notification(
            db,
            event_type="finance.payment.refunded",
            subject="Paiement remboursé",
            message=f"Remboursement de {payment.amount} {payment.currency} effectué : {reason}.",
            school_id=payment.school_id,
            student_id=payment.student_id,
            source_type="school_payment",
            source_id=payment.id,
            current_user=current_user,
        )
    return True


def _check_payment_confirmed(payment: models.SchoolPayment) -> bool:
    """Check if a payment is confirmed (successful)."""
    return (payment.status or "").lower() == "successful"


# ============ Platform payment helpers (for AI credits, subscriptions) ============

def apply_platform_payment(
    db: Session,
    payment: models.PlatformPayment,
    *,
    status: str,
    provider_reference: Optional[str] = None,
    current_user: Optional[models.User] = None,
    extra_metadata: Optional[dict] = None,
) -> bool:
    """Idempotently apply a platform payment status. Mirrors `apply_school_payment`."""
    if provider_reference:
        payment.provider_reference = provider_reference

    if extra_metadata:
        payment.metadata_json = {**(payment.metadata_json or {}), **extra_metadata}

    normalized = (status or "").lower()
    if normalized != "successful":
        payment.status = normalized or payment.status
        return False

    if payment.status == "successful":
        return False

    payment.status = "successful"

    # Handle subscription activation for platform payments with type "subscription"
    if payment.payment_type == "subscription":
        subscription = (
            db.query(models.SchoolSubscription)
            .filter(models.SchoolSubscription.payment_reference == payment.reference)
            .first()
        )
        if subscription:
            now = datetime.now(timezone.utc)
            subscription.status = "active"
            subscription.started_at = now
            # Set next renewal based on billing cycle
            if subscription.billing_cycle == "yearly":
                subscription.next_renewal_at = now + timedelta(days=365)
            else:
                subscription.next_renewal_at = now + timedelta(days=30)
            # Update school subscription fields
            school = db.query(models.School).filter(models.School.id == payment.school_id).first()
            if school:
                school.subscription_status = "active"
                school.subscription_plan = subscription.plan
                school.current_billing_period_end = subscription.next_renewal_at

    # Platform payments don't have invoices — they credit AI wallet or activate subscription
    # Handled by the webhook caller (ai_billing.py)

    audit.record_audit(
        db,
        action="platform.payment.confirmed",
        current_user=current_user,
        entity_type="platform_payment",
        entity_id=payment.reference,
        details={
            "amount": payment.amount,
            "currency": payment.currency,
            "provider": payment.provider,
            "payment_type": payment.payment_type,
        },
    )
    return True


def get_school_payment_methods(db: Session, school_id: int) -> list[dict]:
    """Return the user-facing payment method catalog for a school."""
    providers = enabled_providers(db, school_id)
    methods = []
    for provider in providers:
        if provider == "cinetpay":
            for m in MOBILE_MONEY_METHODS:
                methods.append({"key": m["key"], "label": m["label"], "provider": provider})
        elif provider == "stripe":
            methods.append({"key": "card", "label": "Carte bancaire", "provider": "stripe"})
        elif provider == "djamo":
            methods.append({"key": "djamo", "label": "Djamo", "provider": "djamo"})
        elif provider == CASH:
            methods.append({"key": "cash", "label": "Espèces", "provider": CASH})
    return methods


# ============ Value Objects for Money (MONEY-02) ============

class Money:
    """Value Object for monetary amounts - immutable, currency-aware, precision-safe."""
    
    def __init__(self, amount: float, currency: str = "FCFA"):
        self._amount = money.normalize(amount)
        self._currency = currency
    
    @property
    def amount(self) -> float:
        return self._amount
    
    @property
    def currency(self) -> str:
        return self._currency
    
    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")
        return Money(self.amount - other.amount, self.currency)
    
    def __mul__(self, factor: float) -> "Money":
        return Money(self.amount * factor, self.currency)
    
    def __truediv__(self, factor: float) -> "Money":
        if factor == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return Money(self.amount / factor, self.currency)
    
    def is_zero(self) -> bool:
        return money.is_settled(self.amount)
    
    def is_positive(self) -> bool:
        return not money.is_settled(self.amount) and self.amount > 0
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Money):
            return False
        return self.currency == other.currency and money.is_settled(self.amount - other.amount)
    
    def __lt__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount < other.amount
    
    def __le__(self, other: "Money") -> bool:
        return self == other or self < other
    
    def __gt__(self, other: "Money") -> bool:
        return not self <= other
    
    def __ge__(self, other: "Money") -> bool:
        return not self < other
    
    def __repr__(self) -> str:
        return f"Money({self.amount}, '{self.currency}')"


# ============ Value Objects for Domain (Ubiquitous Language) ============

class SchoolContext:
    """Value Object representing the school context - replaces scattered school_id/year params."""
    
    def __init__(self, school_id: int, academic_year_id: int, school_model_assignment_id: Optional[int] = None):
        self._school_id = school_id
        self._academic_year_id = academic_year_id
        self._school_model_assignment_id = school_model_assignment_id
    
    @property
    def school_id(self) -> int:
        return self._school_id
    
    @property
    def academic_year_id(self) -> int:
        return self._academic_year_id
    
    @property
    def school_model_assignment_id(self) -> Optional[int]:
        return self._school_model_assignment_id
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, SchoolContext):
            return False
        return (self.school_id == other.school_id and 
                self.academic_year_id == other.academic_year_id and
                self.school_model_assignment_id == other.school_model_assignment_id)
    
    def __hash__(self) -> int:
        return hash((self.school_id, self.academic_year_id, self.school_model_assignment_id))
    
    def __repr__(self) -> str:
        return f"SchoolContext(school={self.school_id}, year={self.academic_year_id}, model={self.school_model_assignment_id})"


class StudentRef:
    """Value Object for student reference - replaces (student_id, school_id) tuples."""
    
    def __init__(self, student_id: int, school_id: int):
        self._student_id = student_id
        self._school_id = school_id
    
    @property
    def student_id(self) -> int:
        return self._student_id
    
    @property
    def school_id(self) -> int:
        return self._school_id
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, StudentRef):
            return False
        return self.student_id == other.student_id and self.school_id == other.school_id
    
    def __hash__(self) -> int:
        return hash((self.student_id, self.school_id))
    
    def __repr__(self) -> str:
        return f"StudentRef(student={self.student_id}, school={self.school_id})"


class FeeRef:
    """Value Object for fee reference."""
    
    def __init__(self, fee_id: int, school_id: int):
        self._fee_id = fee_id
        self._school_id = school_id
    
    @property
    def fee_id(self) -> int:
        return self._fee_id
    
    @property
    def school_id(self) -> int:
        return self._school_id
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, FeeRef):
            return False
        return self.fee_id == other.fee_id and self.school_id == other.school_id
    
    def __hash__(self) -> int:
        return hash((self.fee_id, self.school_id))
    
    def __repr__(self) -> str:
        return f"FeeRef(fee={self.fee_id}, school={self.school_id})"


# ============ Payment Service with Value Objects ============

def apply_school_payment_vo(
    db: Session,
    payment: models.SchoolPayment,
    *,
    status: str,
    provider_reference: Optional[str] = None,
    current_user: Optional[models.User] = None,
) -> bool:
    """Idempotently apply a payment status using Value Objects internally."""
    if provider_reference:
        payment.provider_reference = provider_reference

    normalized = (status or "").lower()
    if normalized != "successful":
        payment.status = normalized or payment.status
        return False

    if payment.status == "successful":
        return False

    payment.status = "successful"

    if payment.invoice_id:
        invoice = (
            db.query(models.StudentInvoice)
            .filter(models.StudentInvoice.id == payment.invoice_id, models.StudentInvoice.school_id == payment.school_id)
            .first()
        )
        if invoice:
            # Use Money VO for calculations
            amount = Money(payment.amount, payment.currency)
            paid = Money(invoice.amount_paid or 0, invoice.currency)
            due = Money(invoice.amount_due, invoice.currency)
            
            new_paid = paid + amount
            invoice.amount_paid = money.normalize(new_paid.amount)
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


# ============ Module exports ============

__all__ = [
    # Core functions
    "apply_school_payment",
    "generate_school_payment_receipt",
    "refund_school_payment",
    "apply_platform_payment",
    "get_school_payment_methods",
    "enabled_providers",
    "is_provider_enabled",
    "user_facing_method",
    # Value Objects
    "Money",
    "SchoolContext",
    "StudentRef",
    "FeeRef",
    # VO-enabled functions
    "apply_school_payment_vo",
    # Constants
    "CASH",
    "SUPPORTED_PROVIDERS",
    "MOBILE_MONEY_METHODS",
]