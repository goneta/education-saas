"""MONEY-02 — comparaisons monétaires sur colonnes FLOAT.

The bug is not theoretical: `1.1 + 2.2 == 3.3000000000000003`, so an invoice
paid in full kept a 1e-16 residue, stayed PARTIAL forever and — through
`routers/students.py` — blocked the pupil's certificate although the family had
paid everything.
"""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import money, payment_service


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(s); db.commit()
    return s


def test_float_residue_is_reproducible():
    """The premise: plain float arithmetic really does leave a residue."""
    assert 1.1 + 2.2 != 3.3
    assert (1.1 + 2.2) - 3.3 > 0          # a strictly positive "remaining balance"
    assert money.is_settled((1.1 + 2.2) - 3.3)   # ... which the helper treats as settled


def test_helpers_never_confuse_a_residue_with_a_real_debt():
    assert money.is_settled(0) and money.is_settled(0.004) and money.is_settled(1e-12)
    assert money.is_outstanding(1) and money.is_outstanding(0.5)
    # 1 FCFA — the smallest real amount — is always a real debt.
    assert money.is_outstanding(1.0)
    assert money.normalize(3.3000000000000003) == 3.3
    assert money.remaining(3.3000000000000003, 3.3) == 0.0
    assert money.remaining(100000, 40000) == 60000.0
    assert money.remaining(100, 250) == 0.0     # never negative


def test_invoice_paid_in_two_instalments_becomes_paid_not_partial():
    """The exact production scenario: two payments summing to the invoice with
    a float residue. Before the fix the invoice stayed PARTIAL."""
    db = _session()
    school = _school(db)
    invoice = models.StudentInvoice(
        school_id=school.id, invoice_number=f"INV-{uuid.uuid4().hex[:6]}", title="Scolarité",
        amount_due=3.3, amount_paid=0, remaining_balance=3.3,
        status=models.StudentInvoiceStatus.UNPAID,
    )
    db.add(invoice); db.commit()

    for amount in (1.1, 2.2):
        payment = models.SchoolPayment(
            reference=f"SCH-{uuid.uuid4().hex[:8].upper()}", school_id=school.id,
            payment_type="tuition", amount=amount, currency="FCFA", provider="cash",
            status="pending", invoice_id=invoice.id,
        )
        db.add(payment); db.commit()
        payment_service.apply_school_payment(db, payment, status="successful")
        db.commit()

    db.refresh(invoice)
    assert invoice.remaining_balance == 0.0
    assert invoice.status == models.StudentInvoiceStatus.PAID
    assert invoice.amount_paid == 3.3


def test_partial_payment_still_reads_as_partial():
    """The tolerance must not turn a real debt into a settled invoice."""
    db = _session()
    school = _school(db)
    invoice = models.StudentInvoice(
        school_id=school.id, invoice_number=f"INV-{uuid.uuid4().hex[:6]}", title="Scolarité",
        amount_due=50000, amount_paid=0, remaining_balance=50000,
        status=models.StudentInvoiceStatus.UNPAID,
    )
    db.add(invoice); db.commit()
    payment = models.SchoolPayment(
        reference=f"SCH-{uuid.uuid4().hex[:8].upper()}", school_id=school.id,
        payment_type="tuition", amount=49999, currency="FCFA", provider="cash",
        status="pending", invoice_id=invoice.id,
    )
    db.add(payment); db.commit()
    payment_service.apply_school_payment(db, payment, status="successful")
    db.commit()

    db.refresh(invoice)
    assert invoice.remaining_balance == 1.0            # 1 FCFA is still owed
    assert invoice.status == models.StudentInvoiceStatus.PARTIAL
    assert money.is_outstanding(invoice.remaining_balance)


def test_refund_restores_a_coherent_balance():
    db = _session()
    school = _school(db)
    admin = models.User(email=f"a_{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", full_name="A",
                        role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    invoice = models.StudentInvoice(
        school_id=school.id, invoice_number=f"INV-{uuid.uuid4().hex[:6]}", title="Scolarité",
        amount_due=3.3, amount_paid=0, remaining_balance=3.3,
        status=models.StudentInvoiceStatus.UNPAID,
    )
    db.add_all([admin, invoice]); db.commit()
    payment = models.SchoolPayment(
        reference=f"SCH-{uuid.uuid4().hex[:8].upper()}", school_id=school.id,
        payment_type="tuition", amount=3.3, currency="FCFA", provider="cash",
        status="pending", invoice_id=invoice.id,
    )
    db.add(payment); db.commit()
    payment_service.apply_school_payment(db, payment, status="successful")
    db.commit()
    db.refresh(invoice)
    assert invoice.status == models.StudentInvoiceStatus.PAID

    payment_service.refund_school_payment(db, payment, current_user=admin)
    db.commit()
    db.refresh(invoice)
    assert invoice.amount_paid == 0.0
    assert invoice.remaining_balance == 3.3
    assert invoice.status == models.StudentInvoiceStatus.UNPAID
