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


def test_payment_methods_crud_and_default_promotion():
    db = _session()
    school = _school(db)
    admin = _user(db, school)

    # First method becomes default automatically; last4 sanitized to 4 digits.
    m1 = R.add_payment_method(schemas.PaymentMethodCreate(provider="visa", brand="Visa",
         last4="4242 4242 4242 4242", expiry_month=12, expiry_year=2030, nickname="Main"),
         school_id=None, db=db, current_user=admin)
    assert m1["is_default"] is True
    assert m1["last4"] == "4242"

    m2 = R.add_payment_method(schemas.PaymentMethodCreate(provider="cinetpay", method_type="mobile_money",
         nickname="Wave"), school_id=None, db=db, current_user=admin)
    assert m2["is_default"] is False

    # Set m2 default -> m1 loses default.
    R.set_default_payment_method(m2["id"], school_id=None, db=db, current_user=admin)
    listed = R.list_payment_methods(school_id=None, db=db, current_user=admin)["methods"]
    by_id = {m["id"]: m for m in listed}
    assert by_id[m2["id"]]["is_default"] is True
    assert by_id[m1["id"]]["is_default"] is False
    assert listed[0]["is_default"] is True  # default sorted first

    # Update nickname.
    upd = R.update_payment_method(m1["id"], schemas.PaymentMethodUpdate(nickname="Backup"),
         school_id=None, db=db, current_user=admin)
    assert upd["nickname"] == "Backup"

    # Remove the default (m2) -> the remaining method is promoted to default.
    R.remove_payment_method(m2["id"], school_id=None, db=db, current_user=admin)
    remaining = R.list_payment_methods(school_id=None, db=db, current_user=admin)["methods"]
    assert len(remaining) == 1
    assert remaining[0]["id"] == m1["id"]
    assert remaining[0]["is_default"] is True

    # Unknown method -> 404.
    with pytest.raises(HTTPException) as exc:
        R.set_default_payment_method(999999, school_id=None, db=db, current_user=admin)
    assert exc.value.status_code == 404


def test_payment_method_expiry_state():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    expired = R.add_payment_method(schemas.PaymentMethodCreate(provider="visa", last4="1111",
              expiry_month=1, expiry_year=2020), school_id=None, db=db, current_user=admin)
    assert expired["expiry_state"] == "expired"


def test_billing_assistant_grounds_on_real_data(monkeypatch):
    from backend.services.ai_service import ai_service
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    # Caller needs AI credits (ensure_credits gate).
    wallet = ai_credits.wallet_for_user(db, admin)
    wallet.balance_credits = 1000
    db.add(models.SchoolSubscription(school_id=school.id, plan="pro", billing_cycle="monthly",
                                     amount=99000, currency="FCFA", status="active"))
    db.add(models.PlatformPayment(reference="P-A", school_id=school.id, payment_type="subscription",
                                  amount=99000, currency="FCFA", provider="stripe", status="successful",
                                  beneficiary_entity="platform"))
    db.commit()

    captured = {}

    def fake_ai(prompt, config, dbsession):
        captured["prompt"] = prompt
        captured["module"] = config.get("module")
        return {"data": "Your spend is stable this month."}

    monkeypatch.setattr(ai_service, "generate_response_from_config", fake_ai)
    out = R.ask_assistant(schemas.BillingAssistantRequest(question="Why is my bill higher?", language="en"),
                          school_id=None, db=db, current_user=admin)
    assert out["answer"] == "Your spend is stable this month."
    # The prompt must carry the school's REAL billing data, not invented values.
    assert captured["module"] == "billing_assistant"
    assert "Professional" in captured["prompt"] or "pro" in captured["prompt"]
    assert "this_month_spend" in captured["prompt"]
    # A usage row was recorded (credit-gated call happened).
    assert db.query(models.AIUsageLog).count() >= 1


def test_usage_timeseries_buckets_by_day():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    db.add(models.AIUsageLog(school_id=school.id, module_name="chat", credits_charged=10,
                             total_tokens=500, estimated_cost=1.5, status="successful"))
    db.add(models.AIUsageLog(school_id=school.id, module_name="chat", credits_charged=5,
                             total_tokens=200, estimated_cost=0.5, status="successful"))
    db.add(models.AIUsageLog(school_id=school.id, module_name="ai_learning", credits_charged=7,
                             total_tokens=300, estimated_cost=0.7, status="successful"))
    db.add(models.PlatformPayment(reference="TS-1", school_id=school.id, payment_type="credit_purchase",
                                  amount=25000, currency="FCFA", provider="stripe", status="successful",
                                  beneficiary_entity="platform", credits_amount=500))
    db.commit()

    out = R.get_usage_timeseries(days=30, school_id=None, db=db, current_user=admin)
    assert len(out["series"]) == 30  # continuous x-axis
    assert out["totals"]["credits"] == 22
    assert out["totals"]["requests"] == 3
    assert out["totals"]["tokens"] == 1000
    assert out["totals"]["spend"] == 25000
    # Today's bucket carries the activity.
    today = [b for b in out["series"] if b["credits"] > 0]
    assert today and today[-1]["credits"] == 22
    mods = {m["module"]: m["credits"] for m in out["by_module"]}
    assert mods["chat"] == 15 and mods["ai_learning"] == 7


def test_billing_assistant_empty_question_no_ai():
    db = _session()
    school = _school(db)
    admin = _user(db, school)
    out = R.ask_assistant(schemas.BillingAssistantRequest(question="   "),
                          school_id=None, db=db, current_user=admin)
    assert out["answer"] == ""


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
