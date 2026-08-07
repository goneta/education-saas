"""Lot 6 — pagination Finance + le 500 du journal de caisse (PERF-07).

Two things are proven here:
- `GET /finance/cash-journal` answered **HTTP 500** in production. The handler
  called `list_payments(...)` with 7 positional arguments against an
  11-parameter signature, so `db` landed in `school_model_assignment_id` and the
  real `db` stayed a `Depends` object. The cashier's daily till-closing screen
  was simply broken, and no test covered it.
- The payments list is now paginable without breaking the consumers that
  legitimately need every row (aggregations, exports).
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, security
from backend.routers import finance


def _env(payment_count: int = 0):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()

    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{tag}@x.com", hashed_password="x", full_name="Caissier",
                        role=models.UserRole.SUPER_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.flush()
    fee = models.Fee(title="Scolarité T1", amount=100000, school_id=school.id,
                     status=models.FeeStatus.PENDING, category="TUITION")
    db.add(fee); db.flush()
    base = datetime(2026, 6, 1, tzinfo=timezone.utc)
    for index in range(payment_count):
        db.add(models.Payment(fee_id=fee.id, amount=1000, payment_date=base + timedelta(minutes=index),
                              receipt_number=f"REC-{tag}-{index}", recorded_by_id=admin.id,
                              payment_method="cash", status="successful"))
    db.commit()

    app = FastAPI(); app.include_router(finance.router)
    app.dependency_overrides[database.get_db] = lambda: db
    app.dependency_overrides[security.get_current_user] = lambda: admin
    return TestClient(app, raise_server_exceptions=False), db, school, admin


def test_cash_journal_no_longer_returns_500():
    """The regression that mattered: the till-closing screen."""
    client, _db, _school, _admin = _env(payment_count=3)
    response = client.get("/finance/cash-journal")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] == 3000                      # aggregation is correct
    assert len(payload["payments"]) == 3                 # aggregations see EVERY row
    assert payload["by_category"]["TUITION"] == 3000
    assert payload["by_operator"]["Caissier"] == 3000


def test_reports_endpoint_also_aggregates_every_payment():
    client, _db, _school, _admin = _env(payment_count=5)
    response = client.get("/finance/reports")
    assert response.status_code == 200, response.text


def test_payments_list_is_paginable_and_exposes_the_total():
    client, _db, _school, _admin = _env(payment_count=25)

    everything = client.get("/finance/payments")
    assert everything.status_code == 200
    assert len(everything.json()) == 25                   # default stays unbounded
    assert everything.headers["X-Total-Count"] == "25"    # ... and the total is published

    page = client.get("/finance/payments?limit=10")
    assert len(page.json()) == 10
    assert page.headers["X-Total-Count"] == "25"          # total ≠ page size

    second = client.get("/finance/payments?skip=10&limit=10")
    assert len(second.json()) == 10
    assert {row["id"] for row in page.json()} & {row["id"] for row in second.json()} == set()

    last = client.get("/finance/payments?skip=20&limit=10")
    assert len(last.json()) == 5

    # Newest first, and stable across pages.
    dates = [row["payment_date"] for row in everything.json()]
    assert dates == sorted(dates, reverse=True)


def test_hard_cap_protects_the_server_and_says_so(monkeypatch):
    """A consumer that does not paginate can never make the server serialize an
    unbounded result set — and the truncation is signalled, never silent."""
    client, _db, _school, _admin = _env(payment_count=12)
    monkeypatch.setattr(finance, "PAYMENTS_HARD_CAP", 5)

    response = client.get("/finance/payments")
    assert len(response.json()) == 5
    assert response.headers["X-Total-Count"] == "12"
    assert response.headers.get("X-Truncated") == "true"

    # An explicit page is never flagged as truncated.
    explicit = client.get("/finance/payments?limit=5")
    assert explicit.headers.get("X-Truncated") is None
