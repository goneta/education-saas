"""Enterprise Billing & Subscription service.

This is a *unifying* layer, not a new money system. It aggregates the existing
infrastructure — school subscriptions (`SchoolSubscription`, driven by
`/system/subscription`), AI credit wallets and platform payments
(`AIWallet` / `PlatformPayment` / `AICreditTransaction`, driven by
`/ai_billing`), and the global audit trail (`AuditLog`) — and adds the
configuration the enterprise Billing page needs: billing preferences, tax
identity, wallet auto-recharge and promo codes.

Zero data duplication: subscriptions, wallets, payments and audits are read
from their canonical tables. Invoices and transactions are *projected* from
`PlatformPayment` rather than stored again.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..audit import record_audit
from . import ai_credits


# --- Plan catalog ------------------------------------------------------------
# Mirrors routers.system.SUBSCRIPTION_PRICES (the source of truth used by the
# `/system/subscription/change` endpoint the Subscription tab calls). Prices are
# in the platform base currency (FCFA). Keep the plan *keys* in sync with
# SUBSCRIPTION_PRICES so upgrades route through the existing, tested flow.
PLAN_CATALOG = [
    {
        "key": "free",
        "name": "Starter",
        "monthly": 0,
        "yearly": 0,
        "credits": 200,
        "storage_gb": 5,
        "users": 15,
        "schools": 1,
        "support": "community",
        "features": ["core_sis", "attendance", "grades", "basic_ai"],
    },
    {
        "key": "pro",
        "name": "Professional",
        "monthly": 99000,
        "yearly": 900000,
        "credits": 5000,
        "storage_gb": 100,
        "users": 300,
        "schools": 1,
        "support": "priority_email",
        "features": ["everything_starter", "timetable_ai", "transport", "payroll", "automations", "priority_ai"],
    },
    {
        "key": "max",
        "name": "Enterprise",
        "monthly": 199000,
        "yearly": 1700000,
        "credits": 20000,
        "storage_gb": 1000,
        "users": 5000,
        "schools": 10,
        "support": "dedicated_24_7",
        "features": ["everything_pro", "multi_school", "sso_scim", "api_webhooks", "audit_logs", "sla"],
    },
    {
        "key": "custom",
        "name": "Custom",
        "monthly": None,
        "yearly": None,
        "credits": None,
        "storage_gb": None,
        "users": None,
        "schools": None,
        "support": "dedicated_tam",
        "features": ["unlimited", "custom_contracts", "on_prem_option", "white_label"],
        "contact_sales": True,
    },
]

# Actions considered part of the billing surface for the Audit tab.
BILLING_AUDIT_ACTIONS = (
    "billing.",
    "school.subscription.",
    "platform.payment.",
    "credit.",
)


def current_subscription(db: Session, school_id: int) -> Optional[models.SchoolSubscription]:
    return (
        db.query(models.SchoolSubscription)
        .filter(models.SchoolSubscription.school_id == school_id)
        .order_by(models.SchoolSubscription.created_at.desc(), models.SchoolSubscription.id.desc())
        .first()
    )


def _plan_by_key(key: Optional[str]) -> Optional[dict]:
    return next((p for p in PLAN_CATALOG if p["key"] == key), None)


# --- Preferences -------------------------------------------------------------

def get_preferences(db: Session, school_id: int, *, create: bool = True) -> Optional[models.BillingPreference]:
    pref = db.query(models.BillingPreference).filter(models.BillingPreference.school_id == school_id).first()
    if pref or not create:
        return pref
    school = db.query(models.School).filter(models.School.id == school_id).first()
    pref = models.BillingPreference(
        school_id=school_id,
        currency=(school.default_currency if school else None) or "FCFA",
        timezone=school.timezone if school else None,
        notification_channels={"email": True, "sms": False, "push": True, "inapp": True},
        invoice_recipients=[],
    )
    db.add(pref)
    db.flush()
    return pref


def update_preferences(db: Session, school_id: int, data: dict, user: models.User) -> models.BillingPreference:
    pref = get_preferences(db, school_id)
    for field in (
        "currency", "timezone", "invoice_language", "email_invoices", "payment_reminders",
        "renewal_reminders", "auto_renew", "invoice_recipients", "notification_channels",
    ):
        if field in data and data[field] is not None:
            setattr(pref, field, data[field])
    pref.updated_by_id = user.id
    record_audit(db, action="billing.preferences.updated", current_user=user,
                 entity_type="billing_preference", entity_id=pref.id, details={"school_id": school_id})
    db.flush()
    return pref


# --- Tax profile -------------------------------------------------------------

def get_tax(db: Session, school_id: int, *, create: bool = True) -> Optional[models.BillingTaxProfile]:
    tax = db.query(models.BillingTaxProfile).filter(models.BillingTaxProfile.school_id == school_id).first()
    if tax or not create:
        return tax
    tax = models.BillingTaxProfile(school_id=school_id)
    db.add(tax)
    db.flush()
    return tax


def update_tax(db: Session, school_id: int, data: dict, user: models.User) -> models.BillingTaxProfile:
    tax = get_tax(db, school_id)
    for field in (
        "tax_type", "tax_id", "business_number", "company_registration", "legal_name",
        "tax_rate", "tax_exempt", "billing_address", "shipping_address",
    ):
        if field in data and data[field] is not None:
            setattr(tax, field, data[field])
    tax.updated_by_id = user.id
    record_audit(db, action="billing.tax.updated", current_user=user,
                 entity_type="billing_tax_profile", entity_id=tax.id, details={"school_id": school_id})
    db.flush()
    return tax


# --- Auto-recharge -----------------------------------------------------------

def get_auto_recharge(db: Session, wallet: models.AIWallet, *, create: bool = True) -> Optional[models.WalletAutoRecharge]:
    cfg = db.query(models.WalletAutoRecharge).filter(models.WalletAutoRecharge.wallet_id == wallet.id).first()
    if cfg or not create:
        return cfg
    cfg = models.WalletAutoRecharge(wallet_id=wallet.id, school_id=wallet.school_id)
    db.add(cfg)
    db.flush()
    return cfg


def update_auto_recharge(db: Session, wallet: models.AIWallet, data: dict, user: models.User) -> models.WalletAutoRecharge:
    cfg = get_auto_recharge(db, wallet)
    for field in (
        "enabled", "threshold_credits", "recharge_credits", "recharge_amount", "currency",
        "monthly_max_amount", "pack_id", "payment_provider",
    ):
        if field in data and data[field] is not None:
            setattr(cfg, field, data[field])
    cfg.updated_by_id = user.id
    record_audit(db, action="billing.auto_recharge.updated", current_user=user,
                 entity_type="wallet_auto_recharge", entity_id=cfg.id,
                 details={"enabled": cfg.enabled, "wallet_id": wallet.id})
    db.flush()
    return cfg


# --- Promo codes -------------------------------------------------------------

def _promo_active(promo: models.BillingPromoCode, now: datetime) -> Optional[str]:
    """Return an error reason if the promo cannot be used, else None."""
    if not promo.is_active:
        return "inactive"
    if promo.starts_at and _aware(promo.starts_at) > now:
        return "not_started"
    if promo.expires_at and _aware(promo.expires_at) < now:
        return "expired"
    if promo.max_redemptions is not None and promo.redeemed_count >= promo.max_redemptions:
        return "exhausted"
    return None


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def validate_promo(db: Session, code: str, *, school_id: Optional[int], context: str = "any",
                   base_amount: float = 0.0) -> dict:
    """Validate a code and compute the discount preview (no side effects)."""
    now = datetime.now(timezone.utc)
    promo = db.query(models.BillingPromoCode).filter(
        func.lower(models.BillingPromoCode.code) == code.strip().lower()
    ).first()
    if not promo:
        return {"valid": False, "reason": "not_found"}
    reason = _promo_active(promo, now)
    if reason:
        return {"valid": False, "reason": reason}
    if promo.applies_to != "any" and context != "any" and promo.applies_to != context:
        return {"valid": False, "reason": "wrong_context"}
    if school_id is not None and promo.per_school_limit is not None:
        used = db.query(func.count(models.BillingPromoRedemption.id)).filter(
            models.BillingPromoRedemption.promo_id == promo.id,
            models.BillingPromoRedemption.school_id == school_id,
        ).scalar() or 0
        if used >= promo.per_school_limit:
            return {"valid": False, "reason": "already_used"}
    discount_amount, credits = _compute_discount(promo, base_amount)
    return {
        "valid": True,
        "code": promo.code,
        "kind": promo.kind,
        "discount_type": promo.discount_type,
        "discount_value": promo.discount_value,
        "discount_amount": discount_amount,
        "credits": credits,
        "description": promo.description,
        "promo_id": promo.id,
    }


def _compute_discount(promo: models.BillingPromoCode, base_amount: float) -> tuple[float, int]:
    if promo.discount_type == "percent":
        return round(base_amount * (promo.discount_value / 100.0), 2), 0
    if promo.discount_type == "amount":
        return min(base_amount, promo.discount_value) if base_amount else promo.discount_value, 0
    if promo.discount_type == "credits":
        return 0.0, int(promo.discount_value)
    return 0.0, 0


def redeem_promo(db: Session, code: str, *, school_id: Optional[int], user: models.User,
                 context: str = "any", base_amount: float = 0.0) -> dict:
    """Redeem a code. Credit-type codes top up the school wallet immediately."""
    preview = validate_promo(db, code, school_id=school_id, context=context, base_amount=base_amount)
    if not preview.get("valid"):
        return preview
    promo = db.query(models.BillingPromoCode).filter(models.BillingPromoCode.id == preview["promo_id"]).first()
    credits = int(preview["credits"] or 0)
    if credits and school_id:
        wallet = ai_credits.get_or_create_wallet(db, "school", None, school_id)
        before = wallet.balance_credits
        wallet.balance_credits += credits
        wallet.total_purchased_credits += credits
        db.add(models.AICreditTransaction(
            wallet_id=wallet.id, user_id=user.id, school_id=school_id,
            transaction_type="promo_grant", credits_amount=credits,
            balance_before=before, balance_after=wallet.balance_credits,
            description=f"Promo {promo.code}",
        ))
    promo.redeemed_count += 1
    redemption = models.BillingPromoRedemption(
        promo_id=promo.id, school_id=school_id, user_id=user.id, context=context,
        amount_discounted=float(preview["discount_amount"] or 0), credits_granted=credits,
    )
    db.add(redemption)
    record_audit(db, action="billing.promo.redeemed", current_user=user,
                 entity_type="billing_promo_code", entity_id=promo.id,
                 details={"code": promo.code, "credits": credits, "discount": preview["discount_amount"]})
    db.flush()
    preview["redeemed"] = True
    return preview


# --- Invoices & transactions (projected from PlatformPayment) ----------------

def _payment_to_invoice(p: models.PlatformPayment) -> dict:
    meta = p.metadata_json or {}
    plan = meta.get("plan")
    if p.payment_type == "subscription":
        description = f"Abonnement {plan.upper()}" if plan else "Abonnement TeducAI"
    elif p.credits_amount:
        description = f"{p.credits_amount} crédits IA"
    else:
        description = p.payment_type
    status_map = {"successful": "paid", "pending": "pending", "pending_payment": "pending",
                  "failed": "failed", "refunded": "refunded", "cancelled": "failed"}
    return {
        "id": p.id,
        "number": p.reference,
        "date": p.created_at,
        "description": description,
        "plan": plan,
        "credits": p.credits_amount or 0,
        "amount": p.amount,
        "currency": p.currency,
        "provider": p.provider,
        "status": status_map.get(p.status, p.status),
        "payment_type": p.payment_type,
    }


def list_invoices(db: Session, school_id: int, *, status: Optional[str] = None, limit: int = 100) -> list[dict]:
    q = db.query(models.PlatformPayment).filter(models.PlatformPayment.school_id == school_id)
    rows = q.order_by(models.PlatformPayment.created_at.desc()).limit(limit).all()
    invoices = [_payment_to_invoice(p) for p in rows]
    if status:
        invoices = [i for i in invoices if i["status"] == status]
    return invoices


def list_transactions(db: Session, school_id: int, *, status: Optional[str] = None,
                      payment_type: Optional[str] = None, limit: int = 200) -> list[dict]:
    q = db.query(models.PlatformPayment).filter(models.PlatformPayment.school_id == school_id)
    if payment_type:
        q = q.filter(models.PlatformPayment.payment_type == payment_type)
    rows = q.order_by(models.PlatformPayment.created_at.desc()).limit(limit).all()
    txns = [_payment_to_invoice(p) for p in rows]
    if status:
        txns = [t for t in txns if t["status"] == status]
    return txns


# --- Overview aggregation ----------------------------------------------------

def overview(db: Session, school_id: int) -> dict:
    sub = current_subscription(db, school_id)
    plan_key = sub.plan if sub else "free"
    plan_meta = _plan_by_key(plan_key) or _plan_by_key("free")
    wallet = ai_credits.get_or_create_wallet(db, "school", None, school_id)
    auto = get_auto_recharge(db, wallet, create=False)
    pref = get_preferences(db, school_id, create=False)
    usage = ai_credits.usage_summary(db, school_id=school_id)
    recent = list_transactions(db, school_id, limit=5)
    return {
        "subscription": {
            "plan": plan_key,
            "plan_name": plan_meta["name"] if plan_meta else plan_key,
            "billing_cycle": sub.billing_cycle if sub else "monthly",
            "amount": sub.amount if sub else 0,
            "currency": (sub.currency if sub else None) or (pref.currency if pref else "FCFA"),
            "status": sub.status if sub else "active",
            "next_renewal_at": sub.next_renewal_at if sub else None,
        },
        "wallet": {
            "balance_credits": wallet.balance_credits,
            "total_purchased_credits": wallet.total_purchased_credits,
            "total_used_credits": wallet.total_used_credits,
            "status": wallet.status,
        },
        "auto_recharge": {
            "enabled": bool(auto.enabled) if auto else False,
            "threshold_credits": auto.threshold_credits if auto else 0,
            "recharge_credits": auto.recharge_credits if auto else 0,
            "recharge_amount": auto.recharge_amount if auto else 0,
            "monthly_max_amount": auto.monthly_max_amount if auto else None,
        },
        "usage": usage,
        "recent_transactions": recent,
        "currency": (pref.currency if pref else None) or (sub.currency if sub else "FCFA"),
    }


# --- Audit trail (billing subset) --------------------------------------------

def list_audit(db: Session, *, school_id: Optional[int], limit: int = 100) -> list[models.AuditLog]:
    q = db.query(models.AuditLog)
    if school_id is not None:
        q = q.filter(models.AuditLog.school_id == school_id)
    clauses = [models.AuditLog.action.like(f"{prefix}%") for prefix in BILLING_AUDIT_ACTIONS]
    from sqlalchemy import or_
    q = q.filter(or_(*clauses))
    return q.order_by(models.AuditLog.created_at.desc()).limit(limit).all()


# --- Super-admin revenue -----------------------------------------------------

def revenue_summary(db: Session) -> dict:
    paid = db.query(models.PlatformPayment).filter(models.PlatformPayment.status == "successful")
    total = float(paid.with_entities(func.coalesce(func.sum(models.PlatformPayment.amount), 0)).scalar() or 0)
    subs = db.query(models.SchoolSubscription).filter(models.SchoolSubscription.status == "active")
    mrr = 0.0
    for s in subs.all():
        if not s.amount:
            continue
        mrr += float(s.amount) / (12.0 if s.billing_cycle == "yearly" else 1.0)
    by_country_rows = (
        paid.with_entities(models.PlatformPayment.country_code,
                           func.coalesce(func.sum(models.PlatformPayment.amount), 0))
        .group_by(models.PlatformPayment.country_code).all()
    )
    outstanding = float(
        db.query(func.coalesce(func.sum(models.PlatformPayment.amount), 0))
        .filter(models.PlatformPayment.status.in_(["pending", "pending_payment"])).scalar() or 0
    )
    failed = int(
        db.query(func.count(models.PlatformPayment.id))
        .filter(models.PlatformPayment.status == "failed").scalar() or 0
    )
    schools = int(db.query(func.count(models.School.id)).scalar() or 0)
    return {
        "total_revenue": total,
        "mrr": round(mrr, 2),
        "arr": round(mrr * 12, 2),
        "total_schools": schools,
        "outstanding": outstanding,
        "failed_payments": failed,
        "revenue_by_country": [{"country": c or "—", "amount": float(a)} for c, a in by_country_rows],
    }


# --- Invoice detail + PDF ----------------------------------------------------
# The platform (TeducAI) is the vendor; the school is the customer. An invoice
# is one PlatformPayment rendered as a proper document. Tax is derived from the
# school's BillingTaxProfile (treated as tax-inclusive on the charged amount).

PLATFORM_ISSUER = {
    "name": "TeducAI",
    "tagline": "AI-first education platform",
    "email": "billing@teducai.com",
    "website": "teducai.com",
}


def invoice_detail(db: Session, school_id: int, payment_id: int) -> dict:
    payment = (
        db.query(models.PlatformPayment)
        .filter(models.PlatformPayment.id == payment_id, models.PlatformPayment.school_id == school_id)
        .first()
    )
    if not payment:
        return {}
    school = db.query(models.School).filter(models.School.id == school_id).first()
    tax = get_tax(db, school_id, create=False)
    projected = _payment_to_invoice(payment)
    total = float(payment.amount or 0)
    meta = payment.metadata_json or {}
    discount = float(meta.get("discount") or 0)
    rate = float(tax.tax_rate) if (tax and not tax.tax_exempt) else 0.0
    # Amount charged is tax-inclusive: back out the tax portion.
    net = total - discount
    tax_amount = round(net - net / (1 + rate / 100.0), 2) if rate else 0.0
    subtotal = round(net - tax_amount, 2)
    return {
        "issuer": PLATFORM_ISSUER,
        "customer": {
            "name": school.name if school else "-",
            "address": (school.formatted_address or school.address) if school else None,
            "email": school.email if school else None,
            "phone": school.phone if school else None,
            "registration_number": school.registration_number if school else None,
            "country_code": school.country_code if school else None,
            "tax_id": tax.tax_id if tax else None,
            "legal_name": tax.legal_name if tax else None,
            "business_number": tax.business_number if tax else None,
            "tax_exempt": bool(tax.tax_exempt) if tax else False,
        },
        "number": projected["number"],
        "date": payment.created_at,
        "status": projected["status"],
        "provider": payment.provider,
        "currency": payment.currency,
        "line_items": [{
            "description": projected["description"],
            "credits": payment.credits_amount or 0,
            "quantity": 1,
            "unit_price": subtotal,
            "amount": subtotal,
        }],
        "subtotal": subtotal,
        "discount": discount,
        "tax_rate": rate,
        "tax_amount": tax_amount,
        "total": total,
        "verify_reference": payment.reference,
    }


def _money(n: float, currency: str) -> str:
    return f"{n:,.0f} {currency}" if abs(n) >= 1000 else f"{n:,.2f} {currency}"


def render_invoice_pdf(detail: dict) -> bytes:
    """Render an invoice dict to a real PDF (reportlab, pure-Python)."""
    import io

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as pdfcanvas
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF

    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=A4)
    w, h = A4
    cur = detail.get("currency") or "FCFA"
    left, right = 20 * mm, w - 20 * mm
    y = h - 25 * mm

    issuer = detail.get("issuer", {})
    customer = detail.get("customer", {})

    # Header - issuer + INVOICE title
    c.setFillColorRGB(0.06, 0.06, 0.06)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(left, y, str(issuer.get("name", "TeducAI")))
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.drawString(left, y - 6 * mm, str(issuer.get("tagline", "")))
    c.drawString(left, y - 10 * mm, f"{issuer.get('email','')}  -  {issuer.get('website','')}")
    c.setFillColorRGB(0.06, 0.06, 0.06)
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(right, y, "INVOICE")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawRightString(right, y - 6 * mm, f"#{detail.get('number','')}")
    date = detail.get("date")
    date_str = date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date or "")
    c.drawRightString(right, y - 11 * mm, date_str)

    # Status pill
    status = str(detail.get("status", "")).upper()
    pill = {"PAID": (0.06, 0.5, 0.3), "PENDING": (0.7, 0.5, 0.05), "FAILED": (0.7, 0.15, 0.15)}.get(status, (0.4, 0.4, 0.4))
    c.setFillColorRGB(*pill)
    c.roundRect(right - 30 * mm, y - 20 * mm, 30 * mm, 6 * mm, 3, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(right - 15 * mm, y - 18.2 * mm, status)

    # Bill-to block
    y -= 32 * mm
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(left, y, "BILL TO")
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left, y - 6 * mm, str(customer.get("legal_name") or customer.get("name") or "-"))
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    line = y - 11 * mm
    for txt in [customer.get("address"), customer.get("email"),
                (f"Reg. {customer.get('registration_number')}" if customer.get("registration_number") else None),
                (f"Tax ID {customer.get('tax_id')}" if customer.get("tax_id") else None)]:
        if txt:
            c.drawString(left, line, str(txt))
            line -= 5 * mm

    # Line-items table
    y = line - 8 * mm
    c.setFillColorRGB(0.95, 0.96, 0.97)
    c.rect(left, y - 2 * mm, right - left, 8 * mm, fill=1, stroke=0)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left + 2 * mm, y, "DESCRIPTION")
    c.drawRightString(right - 35 * mm, y, "CREDITS")
    c.drawRightString(right - 2 * mm, y, "AMOUNT")
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    for item in detail.get("line_items", []):
        c.drawString(left + 2 * mm, y, str(item.get("description", "")))
        c.drawRightString(right - 35 * mm, y, str(item.get("credits") or "-"))
        c.drawRightString(right - 2 * mm, y, _money(float(item.get("amount", 0)), cur))
        y -= 8 * mm

    # Totals
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(right - 70 * mm, y, right, y)
    y -= 7 * mm
    rows = [("Subtotal", detail.get("subtotal", 0))]
    if detail.get("discount"):
        rows.append(("Discount", -float(detail.get("discount", 0))))
    if detail.get("tax_amount"):
        rows.append((f"Tax ({detail.get('tax_rate', 0):g}%)", detail.get("tax_amount", 0)))
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    for label, val in rows:
        c.drawString(right - 70 * mm, y, label)
        c.drawRightString(right, y, _money(float(val), cur))
        y -= 6 * mm
    c.setFont("Helvetica-Bold", 13)
    c.setFillColorRGB(0.06, 0.06, 0.06)
    c.drawString(right - 70 * mm, y - 2 * mm, "TOTAL")
    c.drawRightString(right, y - 2 * mm, _money(float(detail.get("total", 0)), cur))

    # QR code (encodes the verifiable reference) + payment method
    qr_widget = qr.QrCodeWidget(str(detail.get("verify_reference", "")))
    bounds = qr_widget.getBounds()
    qw, qh = bounds[2] - bounds[0], bounds[3] - bounds[1]
    size = 26 * mm
    d = Drawing(size, size, transform=[size / qw, 0, 0, size / qh, 0, 0])
    d.add(qr_widget)
    renderPDF.draw(d, c, left, 22 * mm)
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(left, 20 * mm, f"Ref: {detail.get('verify_reference','')}")
    c.drawString(left + size + 6 * mm, 40 * mm, f"Payment method: {detail.get('provider','') or '-'}")
    c.drawString(left + size + 6 * mm, 35 * mm, "Thank you for using TeducAI.")

    # Footer
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawCentredString(w / 2, 12 * mm, f"{issuer.get('name','TeducAI')} - {issuer.get('website','')} - Generated by TeducAI Billing")

    c.showPage()
    c.save()
    return buf.getvalue()


# --- Saved payment methods ---------------------------------------------------
# PCI-safe: only display metadata (brand/last4/expiry) + an optional gateway
# token are stored. A raw card number is never accepted or persisted.

def _digits4(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits[-4:] if digits else None


def _method_expiry_state(m: models.BillingPaymentMethod) -> str:
    if not m.expiry_month or not m.expiry_year:
        return "ok"
    now = datetime.now(timezone.utc)
    exp = (int(m.expiry_year), int(m.expiry_month))
    cur = (now.year, now.month)
    if exp < cur:
        return "expired"
    months_left = (exp[0] - cur[0]) * 12 + (exp[1] - cur[1])
    return "expiring_soon" if months_left <= 2 else "ok"


def serialize_method(m: models.BillingPaymentMethod) -> dict:
    return {
        "id": m.id,
        "method_type": m.method_type,
        "provider": m.provider,
        "nickname": m.nickname,
        "holder_name": m.holder_name,
        "brand": m.brand,
        "last4": m.last4,
        "expiry_month": m.expiry_month,
        "expiry_year": m.expiry_year,
        "billing_address": m.billing_address,
        "is_default": m.is_default,
        "status": m.status,
        "expiry_state": _method_expiry_state(m),
    }


def list_payment_methods(db: Session, school_id: int) -> list[dict]:
    rows = (
        db.query(models.BillingPaymentMethod)
        .filter(models.BillingPaymentMethod.school_id == school_id,
                models.BillingPaymentMethod.status == "active")
        .order_by(models.BillingPaymentMethod.is_default.desc(),
                  models.BillingPaymentMethod.created_at.desc())
        .all()
    )
    return [serialize_method(m) for m in rows]


def _active_methods(db: Session, school_id: int):
    return db.query(models.BillingPaymentMethod).filter(
        models.BillingPaymentMethod.school_id == school_id,
        models.BillingPaymentMethod.status == "active",
    )


def add_payment_method(db: Session, school_id: int, data: dict, user: models.User) -> models.BillingPaymentMethod:
    existing = _active_methods(db, school_id).count()
    make_default = bool(data.get("is_default")) or existing == 0
    if make_default:
        _active_methods(db, school_id).update({models.BillingPaymentMethod.is_default: False})
    method = models.BillingPaymentMethod(
        school_id=school_id,
        method_type=data.get("method_type") or "card",
        provider=data["provider"],
        nickname=data.get("nickname"),
        holder_name=data.get("holder_name"),
        brand=data.get("brand"),
        last4=_digits4(data.get("last4")),
        expiry_month=data.get("expiry_month"),
        expiry_year=data.get("expiry_year"),
        billing_address=data.get("billing_address"),
        gateway_token=data.get("gateway_token"),
        is_default=make_default,
        created_by_id=user.id,
    )
    db.add(method)
    db.flush()
    record_audit(db, action="billing.payment_method.added", current_user=user,
                 entity_type="billing_payment_method", entity_id=method.id,
                 details={"provider": method.provider, "last4": method.last4, "default": make_default})
    return method


def _get_method(db: Session, school_id: int, method_id: int) -> Optional[models.BillingPaymentMethod]:
    return _active_methods(db, school_id).filter(models.BillingPaymentMethod.id == method_id).first()


def update_payment_method(db: Session, school_id: int, method_id: int, data: dict, user: models.User) -> Optional[models.BillingPaymentMethod]:
    method = _get_method(db, school_id, method_id)
    if not method:
        return None
    for field in ("nickname", "holder_name", "brand", "expiry_month", "expiry_year", "billing_address"):
        if field in data and data[field] is not None:
            setattr(method, field, data[field])
    if data.get("last4") is not None:
        method.last4 = _digits4(data.get("last4"))
    if data.get("is_default"):
        _active_methods(db, school_id).update({models.BillingPaymentMethod.is_default: False})
        method.is_default = True
    record_audit(db, action="billing.payment_method.updated", current_user=user,
                 entity_type="billing_payment_method", entity_id=method.id, details={"school_id": school_id})
    db.flush()
    return method


def set_default_payment_method(db: Session, school_id: int, method_id: int, user: models.User) -> Optional[models.BillingPaymentMethod]:
    method = _get_method(db, school_id, method_id)
    if not method:
        return None
    _active_methods(db, school_id).update({models.BillingPaymentMethod.is_default: False})
    method.is_default = True
    record_audit(db, action="billing.payment_method.default", current_user=user,
                 entity_type="billing_payment_method", entity_id=method.id, details={"school_id": school_id})
    db.flush()
    return method


def remove_payment_method(db: Session, school_id: int, method_id: int, user: models.User) -> bool:
    method = _get_method(db, school_id, method_id)
    if not method:
        return False
    was_default = method.is_default
    method.status = "removed"
    method.is_default = False
    db.flush()
    if was_default:
        promoted = _active_methods(db, school_id).order_by(
            models.BillingPaymentMethod.created_at.desc()).first()
        if promoted:
            promoted.is_default = True
    record_audit(db, action="billing.payment_method.removed", current_user=user,
                 entity_type="billing_payment_method", entity_id=method_id, details={"school_id": school_id})
    db.flush()
    return True
