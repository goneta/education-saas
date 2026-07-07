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
