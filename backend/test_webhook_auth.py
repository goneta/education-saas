"""Lot 0 — audit SEC-01 / SEC-02 / CFG-01.

The three production guards that stop money and data from being lost:
- inbound payment webhooks are FAIL-CLOSED (an unconfigured secret can never
  mean "accept anonymous callers" in production);
- the production database URL must be PostgreSQL, never the SQLite fallback.
"""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, webhook_auth
from backend.routers import ai_billing, payments


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


# --- SEC-01: shared-secret verification -------------------------------------

def test_unconfigured_secret_is_rejected_in_production(monkeypatch):
    """The core of SEC-01: no secret + production => 503, never a silent pass."""
    monkeypatch.delenv("SCHOOL_PAYMENT_WEBHOOK_SECRET", raising=False)
    monkeypatch.setattr(database, "is_production", lambda: True)
    with pytest.raises(HTTPException) as exc:
        webhook_auth.verify_shared_secret(None, "SCHOOL_PAYMENT_WEBHOOK_SECRET", purpose="test")
    assert exc.value.status_code == 503  # provider retries once configured
    assert "not configured" in exc.value.detail


def test_unconfigured_secret_is_tolerated_outside_production(monkeypatch):
    monkeypatch.delenv("SCHOOL_PAYMENT_WEBHOOK_SECRET", raising=False)
    monkeypatch.setattr(database, "is_production", lambda: False)
    webhook_auth.verify_shared_secret(None, "SCHOOL_PAYMENT_WEBHOOK_SECRET", purpose="test")


def test_configured_secret_accepts_only_the_exact_value(monkeypatch):
    monkeypatch.setenv("SCHOOL_PAYMENT_WEBHOOK_SECRET", "s3cret")
    monkeypatch.setattr(database, "is_production", lambda: True)
    webhook_auth.verify_shared_secret("s3cret", "SCHOOL_PAYMENT_WEBHOOK_SECRET", purpose="test")
    for forged in (None, "", "s3cre", "S3CRET", "s3cret "):
        with pytest.raises(HTTPException) as exc:
            webhook_auth.verify_shared_secret(forged, "SCHOOL_PAYMENT_WEBHOOK_SECRET", purpose="test")
        assert exc.value.status_code == 403


def test_provider_specific_secret_takes_precedence(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "stripe-only")
    monkeypatch.setenv("SCHOOL_PAYMENT_WEBHOOK_SECRET", "shared")
    monkeypatch.setattr(database, "is_production", lambda: True)
    webhook_auth.verify_shared_secret(
        "stripe-only", "STRIPE_WEBHOOK_SECRET", "SCHOOL_PAYMENT_WEBHOOK_SECRET", purpose="stripe")
    with pytest.raises(HTTPException):
        webhook_auth.verify_shared_secret(
            "shared", "STRIPE_WEBHOOK_SECRET", "SCHOOL_PAYMENT_WEBHOOK_SECRET", purpose="stripe")


# --- SEC-01 at the endpoint level -------------------------------------------

def test_school_payment_webhook_refuses_unauthenticated_call_in_production(monkeypatch):
    """End-to-end guard: the forged confirmation that used to settle an invoice
    for free is now refused before any money side-effect runs."""
    db = _session()
    school = models.School(name="S", domain_prefix=f"s_{uuid.uuid4().hex[:6]}",
                           school_type=models.SchoolType.GENERAL)
    db.add(school); db.commit()
    payment = models.SchoolPayment(
        reference=f"SCH-{uuid.uuid4().hex[:8].upper()}", school_id=school.id,
        payment_type="tuition", amount=50000, currency="FCFA", provider="stripe", status="pending",
    )
    db.add(payment); db.commit()

    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("SCHOOL_PAYMENT_WEBHOOK_SECRET", raising=False)
    monkeypatch.setattr(database, "is_production", lambda: True)

    class _Payload:
        reference = payment.reference
        status = "successful"
        provider_reference = None

    with pytest.raises(HTTPException) as exc:
        payments.payment_webhook("stripe", _Payload(), None, db)
    assert exc.value.status_code == 503
    db.refresh(payment)
    assert payment.status == "pending"  # nothing was applied


def test_platform_webhook_helper_is_fail_closed(monkeypatch):
    monkeypatch.delenv("PLATFORM_PAYMENT_WEBHOOK_SECRET", raising=False)
    monkeypatch.setattr(database, "is_production", lambda: True)
    with pytest.raises(HTTPException) as exc:
        ai_billing._verify_webhook("PLATFORM_PAYMENT_WEBHOOK_SECRET", None)
    assert exc.value.status_code == 503


# --- CFG-01: production database guard --------------------------------------

def test_production_refuses_missing_or_sqlite_database_url():
    with pytest.raises(RuntimeError) as exc:
        database.validate_database_url("sqlite:///./education_saas.db", production=True, configured=False)
    assert "DATABASE_URL must be configured" in str(exc.value)

    with pytest.raises(RuntimeError) as exc:
        database.validate_database_url("sqlite:///./whatever.db", production=True, configured=True)
    assert "PostgreSQL" in str(exc.value)

    # PostgreSQL in production and anything in development are accepted.
    database.validate_database_url("postgresql+psycopg2://u:p@host/db", production=True, configured=True)
    database.validate_database_url("sqlite:///./dev.db", production=False, configured=False)
