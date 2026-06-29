import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import payments
from backend.services import payment_service


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_user(db, role=models.UserRole.ACCOUNTANT):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"P {uid}", domain_prefix=f"p_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    user = models.User(email=f"a_{uid}@p.local", hashed_password="x", full_name="A", role=role, school_id=school.id, is_active=True)
    db.add(user)
    db.commit()
    return school, user


def _invoice_and_payment(db, school, amount=10000.0, provider="cinetpay"):
    invoice = models.StudentInvoice(
        invoice_number=f"INV-{uuid.uuid4().hex[:6]}", title="Tuition",
        amount_due=amount, amount_paid=0, remaining_balance=amount, school_id=school.id,
    )
    db.add(invoice)
    db.flush()
    payment = models.SchoolPayment(
        reference=f"SCH-{uuid.uuid4().hex[:8]}", school_id=school.id, payment_type="school_fee",
        amount=amount, currency="XOF", provider=provider, status="pending", invoice_id=invoice.id,
    )
    db.add(payment)
    db.commit()
    return invoice, payment


def test_webhook_confirms_payment_and_updates_invoice():
    db = _session()
    school, _ = _school_user(db)
    invoice, payment = _invoice_and_payment(db, school)
    out = payments.payment_webhook(
        "cinetpay",
        schemas.SchoolPaymentWebhook(reference=payment.reference, status="successful", provider_reference="cp_123"),
        x_teducai_webhook_secret=None, db=db,
    )
    assert out["applied"] is True and out["status"] == "successful"
    db.refresh(invoice)
    assert invoice.amount_paid == 10000 and invoice.remaining_balance == 0
    assert invoice.status == models.StudentInvoiceStatus.PAID


def test_duplicate_webhook_is_idempotent():
    db = _session()
    school, _ = _school_user(db)
    invoice, payment = _invoice_and_payment(db, school)
    body = schemas.SchoolPaymentWebhook(reference=payment.reference, status="successful")
    first = payments.payment_webhook("cinetpay", body, x_teducai_webhook_secret=None, db=db)
    second = payments.payment_webhook("cinetpay", body, x_teducai_webhook_secret=None, db=db)
    assert first["applied"] is True
    assert second["applied"] is False  # no-op on replay
    db.refresh(invoice)
    assert invoice.amount_paid == 10000  # NOT doubled
    assert invoice.remaining_balance == 0


def test_partial_then_full_payment_status():
    db = _session()
    school, _ = _school_user(db)
    invoice = models.StudentInvoice(invoice_number=f"INV-{uuid.uuid4().hex[:6]}", title="T", amount_due=10000, amount_paid=0, remaining_balance=10000, school_id=school.id)
    db.add(invoice); db.flush()
    p1 = models.SchoolPayment(reference=f"SCH-{uuid.uuid4().hex[:8]}", school_id=school.id, payment_type="school_fee", amount=4000, currency="XOF", provider="cash", status="pending", invoice_id=invoice.id)
    p2 = models.SchoolPayment(reference=f"SCH-{uuid.uuid4().hex[:8]}", school_id=school.id, payment_type="school_fee", amount=6000, currency="XOF", provider="cash", status="pending", invoice_id=invoice.id)
    db.add_all([p1, p2]); db.commit()
    payment_service.apply_school_payment(db, p1, status="successful"); db.commit(); db.refresh(invoice)
    assert invoice.status == models.StudentInvoiceStatus.PARTIAL and invoice.remaining_balance == 6000
    payment_service.apply_school_payment(db, p2, status="successful"); db.commit(); db.refresh(invoice)
    assert invoice.status == models.StudentInvoiceStatus.PAID and invoice.remaining_balance == 0


def test_bad_signature_rejected():
    db = _session()
    school, _ = _school_user(db)
    _invoice, payment = _invoice_and_payment(db, school)
    import os
    os.environ["SCHOOL_PAYMENT_WEBHOOK_SECRET"] = "topsecret"
    try:
        try:
            payments.payment_webhook("cinetpay", schemas.SchoolPaymentWebhook(reference=payment.reference, status="successful"), x_teducai_webhook_secret="wrong", db=db)
            assert False, "bad signature should be rejected"
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 403
    finally:
        del os.environ["SCHOOL_PAYMENT_WEBHOOK_SECRET"]


def test_enabled_providers_reflects_active_accounts():
    db = _session()
    school, _ = _school_user(db)
    db.add(models.SchoolPaymentAccount(school_id=school.id, provider="stripe", account_name="S", is_active=True))
    db.add(models.SchoolPaymentAccount(school_id=school.id, provider="djamo", account_name="D", is_active=False))
    db.commit()
    enabled = payment_service.enabled_providers(db, school.id)
    assert "stripe" in enabled and "cash" in enabled
    assert "djamo" not in enabled  # inactive account excluded


def test_manual_verify_requires_manager_and_confirms():
    db = _session()
    school, accountant = _school_user(db, role=models.UserRole.ACCOUNTANT)
    invoice, payment = _invoice_and_payment(db, school)
    out = payments.manual_verify(payment.reference, current_user=accountant, db=db)
    assert out["applied"] is True
    # A student cannot manually verify.
    student = models.User(email=f"s_{uuid.uuid4().hex[:6]}@p.local", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student); db.commit()
    _i2, p2 = _invoice_and_payment(db, school)
    try:
        payments.manual_verify(p2.reference, current_user=student, db=db)
        assert False, "student should not verify payments"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
