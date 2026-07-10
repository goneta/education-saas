import asyncio
import hashlib
import hmac
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import payments as R
from backend.services import payment_gateway


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(s); db.commit()
    return s


def _user(db, school, role=models.UserRole.CASHIER):
    tag = uuid.uuid4().hex[:5]
    u = models.User(email=f"u_{tag}@x.com", hashed_password="x", full_name="U", role=role,
                    school_id=school.id, is_active=True)
    db.add(u); db.commit()
    return u


def _school_payment(db, school, invoice=None, amount=50000.0):
    row = models.SchoolPayment(
        reference=f"SCH-{uuid.uuid4().hex[:10].upper()}", school_id=school.id,
        payment_type="tuition", amount=amount, currency="FCFA", provider="cinetpay",
        status="pending", invoice_id=invoice.id if invoice else None,
    )
    db.add(row); db.commit()
    return row


class _FakeRequest:
    def __init__(self, form):
        self._form = form
        self.headers = {"content-type": "application/x-www-form-urlencoded"}

    async def form(self):
        return self._form

    async def json(self):  # pragma: no cover
        return self._form


def _notify(db, form, x_token=None):
    return asyncio.get_event_loop().run_until_complete(
        R.cinetpay_notify(_FakeRequest(form), x_token=x_token, db=db)
    )


def test_hmac_token_verification(monkeypatch):
    monkeypatch.setenv("CINETPAY_SECRET_KEY", "topsecret")
    form = {"cpm_site_id": "111", "cpm_trans_id": "SCH-1", "cpm_trans_date": "2026",
            "cpm_amount": "50000", "cpm_currency": "XOF"}
    data = "".join(str(form.get(f, "") or "") for f in payment_gateway.CINETPAY_HMAC_FIELDS)
    good = hmac.new(b"topsecret", data.encode(), hashlib.sha256).hexdigest()
    assert payment_gateway.verify_cinetpay_token(good, form) is True
    assert payment_gateway.verify_cinetpay_token("forged", form) is False
    assert payment_gateway.verify_cinetpay_token(None, form) is False
    monkeypatch.delenv("CINETPAY_SECRET_KEY")
    # No secret configured -> token check passes; the check API stays the gate.
    assert payment_gateway.verify_cinetpay_token(None, form) is True


def test_notify_verifies_with_gateway_and_applies_idempotently(monkeypatch):
    db = _session()
    school = _school(db)
    invoice = models.StudentInvoice(school_id=school.id, invoice_number=f"INV-{uuid.uuid4().hex[:6]}",
                                    title="Scolarite T1", amount_due=50000, amount_paid=0,
                                    remaining_balance=50000, status=models.StudentInvoiceStatus.UNPAID)
    db.add(invoice); db.commit()
    payment = _school_payment(db, school, invoice=invoice)
    monkeypatch.delenv("CINETPAY_SECRET_KEY", raising=False)

    calls = {"n": 0}

    def fake_check(reference):
        calls["n"] += 1
        assert reference == payment.reference
        return "successful", {"code": "00", "data": {"status": "ACCEPTED", "operator_id": "OM-778899",
                                                     "payment_method": "OMCIV2"}}

    monkeypatch.setattr(payment_gateway, "cinetpay_check_transaction", fake_check)
    out = _notify(db, {"cpm_trans_id": payment.reference, "cpm_payid": "PAYID-1"})
    assert out["status"] == "successful" and out["applied"] is True
    db.refresh(invoice)
    # Accounting side-effects ran exactly once: invoice fully paid.
    assert invoice.status == models.StudentInvoiceStatus.PAID
    assert invoice.amount_paid == 50000
    assert payment.provider_reference == "OM-778899"
    assert payment.metadata_json["gateway_check"]["data"]["status"] == "ACCEPTED"

    # Replay/duplicate delivery: re-verified, then idempotent no-op.
    out2 = _notify(db, {"cpm_trans_id": payment.reference})
    assert out2["applied"] is False
    db.refresh(invoice)
    assert invoice.amount_paid == 50000  # NOT double-credited
    assert calls["n"] == 2  # every delivery re-verified against the gateway


def test_notify_rejects_forged_token(monkeypatch):
    db = _session()
    school = _school(db)
    payment = _school_payment(db, school)
    monkeypatch.setenv("CINETPAY_SECRET_KEY", "topsecret")
    monkeypatch.setattr(payment_gateway, "cinetpay_check_transaction",
                        lambda ref: (_ for _ in ()).throw(AssertionError("must not be called")))
    with pytest.raises(HTTPException) as exc:
        _notify(db, {"cpm_trans_id": payment.reference}, x_token="forged")
    assert exc.value.status_code == 403
    assert payment.status == "pending"


def test_notify_never_trusts_body_status(monkeypatch):
    """A notify claiming success is applied as FAILED when the check API refuses."""
    db = _session()
    school = _school(db)
    payment = _school_payment(db, school)
    monkeypatch.delenv("CINETPAY_SECRET_KEY", raising=False)
    monkeypatch.setattr(payment_gateway, "cinetpay_check_transaction",
                        lambda ref: ("failed", {"code": "00", "data": {"status": "REFUSED"}}))
    out = _notify(db, {"cpm_trans_id": payment.reference, "cpm_error_message": "SUCCES"})
    assert out["status"] == "failed" and out["applied"] is False


def test_notify_gateway_unreachable_returns_503(monkeypatch):
    db = _session()
    school = _school(db)
    payment = _school_payment(db, school)
    monkeypatch.delenv("CINETPAY_SECRET_KEY", raising=False)
    monkeypatch.setattr(payment_gateway, "cinetpay_check_transaction",
                        lambda ref: ("unknown", {"message": "gateway unreachable"}))
    with pytest.raises(HTTPException) as exc:
        _notify(db, {"cpm_trans_id": payment.reference})
    assert exc.value.status_code == 503  # CinetPay will retry the delivery
    assert payment.status == "pending"


def test_notify_activates_platform_subscription(monkeypatch):
    db = _session()
    school = _school(db)
    ref = f"SUB-{uuid.uuid4().hex[:10].upper()}"
    db.add(models.PlatformPayment(reference=ref, school_id=school.id, payment_type="subscription",
                                  amount=99000, currency="FCFA", provider="cinetpay",
                                  status="pending_payment", beneficiary_entity="platform"))
    db.add(models.SchoolSubscription(school_id=school.id, plan="pro", billing_cycle="monthly",
                                     amount=99000, currency="FCFA", status="pending_payment",
                                     payment_reference=ref))
    db.commit()
    monkeypatch.delenv("CINETPAY_SECRET_KEY", raising=False)
    monkeypatch.setattr(payment_gateway, "cinetpay_check_transaction",
                        lambda r: ("successful", {"code": "00", "data": {"status": "ACCEPTED"}}))
    out = _notify(db, {"cpm_trans_id": ref})
    assert out["applied"] is True
    sub = db.query(models.SchoolSubscription).filter_by(payment_reference=ref).first()
    assert sub.status == "active" and sub.next_renewal_at is not None
    db.refresh(school)
    assert school.subscription_plan == "pro" and school.subscription_status == "active"


def test_refresh_endpoint_gateway_backed(monkeypatch):
    db = _session()
    school = _school(db)
    cashier = _user(db, school, role=models.UserRole.CASHIER)
    payment = _school_payment(db, school)
    monkeypatch.setattr(payment_gateway, "cinetpay_check_transaction",
                        lambda r: ("successful", {"code": "00", "data": {"status": "ACCEPTED"}}))
    out = R.refresh_payment(payment.reference, current_user=cashier, db=db)
    assert out["status"] == "successful" and out["applied"] is True

    # Unrelated user from another school is rejected.
    other = _user(db, _school(db), role=models.UserRole.CASHIER)
    with pytest.raises(HTTPException) as exc:
        R.refresh_payment(payment.reference, current_user=other, db=db)
    assert exc.value.status_code == 403

    # Non-CinetPay payment -> 400.
    cash = models.SchoolPayment(reference=f"SCH-{uuid.uuid4().hex[:8]}", school_id=school.id,
                                payment_type="tuition", amount=1000, currency="FCFA",
                                provider="cash", status="pending")
    db.add(cash); db.commit()
    with pytest.raises(HTTPException) as exc2:
        R.refresh_payment(cash.reference, current_user=cashier, db=db)
    assert exc2.value.status_code == 400


def test_check_transaction_status_mapping(monkeypatch):
    class FakeResponse:
        status_code = 200
        def __init__(self, payload): self._p = payload
        def json(self): return self._p

    monkeypatch.setenv("CINETPAY_API_KEY", "k")
    monkeypatch.setenv("CINETPAY_SITE_ID", "s")
    for raw, expected in [("ACCEPTED", "successful"), ("REFUSED", "failed"),
                          ("WAITING_FOR_CUSTOMER", "pending")]:
        monkeypatch.setattr(payment_gateway.httpx, "post",
                            lambda *a, _raw=raw, **k: FakeResponse({"code": "00", "data": {"status": _raw}}))
        status, _ = payment_gateway.cinetpay_check_transaction("SCH-X")
        assert status == expected
    # Network failure -> unknown (caller must not apply anything).
    def boom(*a, **k): raise payment_gateway.httpx.ConnectError("down")
    monkeypatch.setattr(payment_gateway.httpx, "post", boom)
    status, payload = payment_gateway.cinetpay_check_transaction("SCH-X")
    assert status == "unknown"
