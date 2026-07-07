import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import billing as R
from backend.services import ai_credits, billing as svc


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL,
                           default_currency="FCFA")
    db.add(school); db.commit()
    return school


def _user(db, school, role=models.UserRole.SCHOOL_ADMIN):
    tag = uuid.uuid4().hex[:5]
    u = models.User(email=f"u_{tag}@x.com", hashed_password="x", full_name="Admin", role=role,
                    school_id=school.id, is_active=True)
    db.add(u); db.commit()
    return u


def test_overview_aggregates_subscription_and_wallet():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    # A subscription + a credit wallet with balance.
    db.add(models.SchoolSubscription(school_id=school.id, plan="pro", billing_cycle="monthly",
                                     amount=99000, currency="FCFA", status="active"))
    wallet = ai_credits.get_or_create_wallet(db, "school", None, school.id)
    wallet.balance_credits = 4200
    db.commit()

    data = R.get_overview(school_id=None, db=db, current_user=admin)
    assert data["subscription"]["plan"] == "pro"
    assert data["subscription"]["plan_name"] == "Professional"
    assert data["wallet"]["balance_credits"] == 4200
    assert "credits_used" in data["usage"]


def test_preferences_get_creates_default_then_update():
    db = _session()
    school = _school(db)
    admin = _user(db, school)

    pref = R.get_preferences(school_id=None, db=db, current_user=admin)
    assert pref.currency == "FCFA"
    assert pref.email_invoices is True

    updated = R.put_preferences(schemas.BillingPreferenceUpdate(invoice_language="en", auto_renew=False,
                                invoice_recipients=["cfo@x.com"]), school_id=None, db=db, current_user=admin)
    assert updated.invoice_language == "en"
    assert updated.auto_renew is False
    assert updated.invoice_recipients == ["cfo@x.com"]
    # Audit row recorded.
    assert db.query(models.AuditLog).filter(models.AuditLog.action == "billing.preferences.updated").count() == 1


def test_tax_profile_upsert():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    tax = R.put_tax(schemas.BillingTaxUpdate(tax_type="vat", tax_id="CI-VAT-99", tax_rate=18.0,
                    billing_address={"line1": "Rue A", "city": "Abidjan"}),
                    school_id=None, db=db, current_user=admin)
    assert tax.tax_id == "CI-VAT-99"
    assert tax.tax_rate == 18.0
    assert tax.billing_address["city"] == "Abidjan"


def test_auto_recharge_upsert_and_overview_reflects_it():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    cfg = R.put_auto_recharge(schemas.AutoRechargeUpdate(enabled=True, threshold_credits=100,
                              recharge_credits=500, recharge_amount=25000, monthly_max_amount=100000),
                              school_id=None, db=db, current_user=admin)
    assert cfg.enabled is True
    assert cfg.recharge_credits == 500
    ov = R.get_overview(school_id=None, db=db, current_user=admin)
    assert ov["auto_recharge"]["enabled"] is True
    assert ov["auto_recharge"]["threshold_credits"] == 100


def test_promo_credits_grant_tops_up_wallet():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    db.add(models.BillingPromoCode(code="WELCOME100", kind="gift", discount_type="credits",
                                   discount_value=100, is_active=True))
    db.commit()

    preview = R.validate_promo(schemas.PromoValidateRequest(code="welcome100"), school_id=None,
                               db=db, current_user=admin)
    assert preview["valid"] is True
    assert preview["credits"] == 100

    result = R.redeem_promo(schemas.PromoValidateRequest(code="WELCOME100"), school_id=None,
                            db=db, current_user=admin)
    assert result["redeemed"] is True
    wallet = ai_credits.get_or_create_wallet(db, "school", None, school.id)
    assert wallet.balance_credits == 100
    # Second redemption blocked by per_school_limit=1 default.
    with pytest.raises(HTTPException) as exc:
        R.redeem_promo(schemas.PromoValidateRequest(code="WELCOME100"), school_id=None,
                       db=db, current_user=admin)
    assert exc.value.status_code == 400


def test_promo_percent_discount_preview():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    db.add(models.BillingPromoCode(code="SAVE20", kind="coupon", discount_type="percent",
                                   discount_value=20, applies_to="subscription", is_active=True))
    db.commit()
    preview = R.validate_promo(schemas.PromoValidateRequest(code="SAVE20", context="subscription",
                               base_amount=99000), school_id=None, db=db, current_user=admin)
    assert preview["valid"] is True
    assert preview["discount_amount"] == 19800.0


def test_invoices_projected_from_platform_payments():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    db.add(models.PlatformPayment(reference="SUB-1", school_id=school.id, payment_type="subscription",
                                  amount=99000, currency="FCFA", provider="stripe", status="successful",
                                  beneficiary_entity="platform", metadata_json={"plan": "pro"}))
    db.add(models.PlatformPayment(reference="CRD-1", school_id=school.id, payment_type="credit_purchase",
                                  amount=25000, currency="FCFA", provider="cinetpay", status="pending",
                                  beneficiary_entity="platform", credits_amount=500))
    db.commit()
    out = R.get_invoices(school_id=None, status=None, limit=100, db=db, current_user=admin)
    invoices = out["invoices"]
    assert len(invoices) == 2
    paid = [i for i in invoices if i["status"] == "paid"]
    assert paid and paid[0]["plan"] == "pro"
    # Status filter works.
    only_paid = R.get_invoices(school_id=None, status="paid", limit=100, db=db, current_user=admin)["invoices"]
    assert len(only_paid) == 1


def test_invoice_detail_and_pdf():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    # Give the school a VAT profile so the invoice shows tax.
    R.put_tax(schemas.BillingTaxUpdate(tax_type="vat", tax_id="CI-VAT-1", tax_rate=18.0),
              school_id=None, db=db, current_user=admin)
    pay = models.PlatformPayment(reference="SUB-9", school_id=school.id, payment_type="subscription",
                                 amount=118000, currency="FCFA", provider="stripe", status="successful",
                                 beneficiary_entity="platform", metadata_json={"plan": "pro"})
    db.add(pay); db.commit()

    detail = R.get_invoice_detail(pay.id, school_id=None, db=db, current_user=admin)
    assert detail["number"] == "SUB-9"
    assert detail["status"] == "paid"
    assert detail["customer"]["tax_id"] == "CI-VAT-1"
    # Tax-inclusive: 118000 total @18% -> tax 18000, subtotal 100000.
    assert round(detail["tax_amount"]) == 18000
    assert round(detail["subtotal"]) == 100000
    assert detail["total"] == 118000

    resp = R.get_invoice_pdf(pay.id, school_id=None, db=db, current_user=admin)
    assert resp.media_type == "application/pdf"
    assert resp.body[:4] == b"%PDF"
    assert "SUB-9" in resp.headers["Content-Disposition"]

    # Unknown / cross-school invoice -> 404.
    with pytest.raises(HTTPException) as exc:
        R.get_invoice_detail(999999, school_id=None, db=db, current_user=admin)
    assert exc.value.status_code == 404


def test_rbac_teacher_blocked_super_admin_revenue():
    db = _session()
    school = _school(db)
    teacher = _user(db, school, role=models.UserRole.TEACHER)
    with pytest.raises(HTTPException) as exc:
        R.get_overview(school_id=None, db=db, current_user=teacher)
    assert exc.value.status_code == 403
    # Non-super-admin blocked from revenue.
    admin = _user(db, school, role=models.UserRole.SCHOOL_ADMIN)
    with pytest.raises(HTTPException) as exc2:
        R.get_revenue(db=db, current_user=admin)
    assert exc2.value.status_code == 403


def test_super_admin_revenue_summary():
    db = _session()
    school = _school(db)
    super_admin = models.User(email=f"sa_{uuid.uuid4().hex[:5]}@x.com", hashed_password="x",
                              full_name="SA", role=models.UserRole.SUPER_ADMIN, is_active=True)
    db.add(super_admin)
    db.add(models.SchoolSubscription(school_id=school.id, plan="pro", billing_cycle="monthly",
                                     amount=99000, currency="FCFA", status="active"))
    db.add(models.PlatformPayment(reference="P1", school_id=school.id, payment_type="subscription",
                                  amount=99000, currency="FCFA", country_code="CI", provider="stripe",
                                  status="successful", beneficiary_entity="platform"))
    db.commit()
    rev = R.get_revenue(db=db, current_user=super_admin)
    assert rev["total_revenue"] == 99000
    assert rev["mrr"] == 99000
    assert rev["arr"] == 99000 * 12
    assert rev["total_schools"] == 1
    assert any(r["country"] == "CI" for r in rev["revenue_by_country"])


def test_super_admin_creates_and_lists_promo():
    db = _session()
    super_admin = models.User(email=f"sa_{uuid.uuid4().hex[:5]}@x.com", hashed_password="x",
                              full_name="SA", role=models.UserRole.SUPER_ADMIN, is_active=True)
    db.add(super_admin); db.commit()
    promo = R.create_promo(schemas.PromoCodeCreate(code="LAUNCH", kind="promo", discount_type="percent",
                           discount_value=15), db=db, current_user=super_admin)
    assert promo.code == "LAUNCH"
    with pytest.raises(HTTPException) as exc:
        R.create_promo(schemas.PromoCodeCreate(code="LAUNCH"), db=db, current_user=super_admin)
    assert exc.value.status_code == 409
    listed = R.list_promos(db=db, current_user=super_admin)
    assert len(listed) == 1
