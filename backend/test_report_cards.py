"""Lot 4 — audit FONC-01 / OPS-02 : bulletin imprimable et livraison des webhooks."""

import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import report_cards, webhook_dispatch


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


class _Report:
    """Stand-in for schemas.ReportCardResponse (only the fields the PDF reads)."""
    def __init__(self, subjects, overall_average):
        self.subjects = subjects
        self.overall_average = overall_average


class _Subject:
    def __init__(self, name, coefficient, average, assessments):
        self.subject_name = name
        self.coefficient = coefficient
        self.average = average
        self.assessments = assessments


def _student(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"Lycée {tag}", domain_prefix=f"s_{tag}",
                           school_type=models.SchoolType.GENERAL, address="Abidjan")
    db.add(school); db.flush()
    user = models.User(email=f"e_{tag}@x.com", hashed_password="x", full_name="Awa Traoré",
                       role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    cls = models.Class(name="3ème A", level="3EME", school_id=school.id)
    db.add(cls); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"MAT-{tag}",
                                    current_class_id=cls.id)
    db.add(profile); db.flush()
    term = models.Term(name="Trimestre 2")
    db.add(term); db.commit()
    return profile, term, school


def test_report_card_pdf_is_a_real_pdf_with_the_student_data():
    db = _session()
    profile, term, school = _student(db)
    report = _Report([
        _Subject("Mathématiques", 4, 15.25, [1, 2]),
        _Subject("Français", 3, 11.5, [1]),
    ], overall_average=13.6)

    context = report_cards.build_context(db, profile=profile, term_id=term.id, report=report)
    assert context["student_name"] == "Awa Traoré"
    assert context["class_name"] == "3ème A"
    assert context["term_name"] == "Trimestre 2"
    assert context["mention"] == "Assez bien"          # 13.6 -> Assez bien
    assert len(context["subjects"]) == 2

    context = report_cards.attach_registry(db, context)
    db.commit()
    assert context["uuid"] and context["verify_url"].endswith(context["uuid"])
    # The bulletin is registered, so its QR resolves on the public verify page.
    registered = db.query(models.DocumentRegistry).filter_by(source_type="report_card").all()
    assert len(registered) == 1 and registered[0].document_type == "report_card"

    pdf = report_cards.render_pdf(context)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000

    # Regenerating the same bulletin keeps ONE registry entry (idempotent).
    report_cards.attach_registry(db, report_cards.build_context(
        db, profile=profile, term_id=term.id, report=report))
    db.commit()
    assert db.query(models.DocumentRegistry).filter_by(source_type="report_card").count() == 1


def test_report_card_pdf_handles_a_term_without_grades():
    db = _session()
    profile, term, _school = _student(db)
    context = report_cards.build_context(db, profile=profile, term_id=term.id,
                                         report=_Report([], overall_average=0))
    pdf = report_cards.render_pdf(context)
    assert pdf.startswith(b"%PDF")  # renders an explicit "no grades" bulletin


# --- OPS-02: outbound webhook delivery ---------------------------------------

def _delivery(db, url="https://partner.example/hook", secret="s3cret", status="pending"):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    endpoint = models.WebhookEndpoint(school_id=school.id, url=url, secret=secret,
                                      event_types=["announcement.published"], is_active=True)
    db.add(endpoint); db.flush()
    delivery = models.WebhookDelivery(endpoint_id=endpoint.id, school_id=school.id,
                                      event_type="announcement.published", payload={"id": 1},
                                      status=status, attempts=0, max_attempts=3)
    db.add(delivery); db.commit()
    return delivery, endpoint


def test_delivery_is_sent_and_signed():
    db = _session()
    delivery, endpoint = _delivery(db)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["signature"] = request.headers.get("x-teducai-signature")
        seen["body"] = request.content
        return httpx.Response(200)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    summary = webhook_dispatch.dispatch_pending(db, client=client)

    assert summary["delivered"] == 1
    db.refresh(delivery)
    assert delivery.status == "delivered" and delivery.last_error is None
    assert seen["url"] == endpoint.url
    # The receiver can authenticate us: HMAC-SHA256 of the exact body.
    assert seen["signature"] == webhook_dispatch.sign_payload(endpoint.secret, seen["body"])


def test_failed_delivery_backs_off_then_fails_definitively():
    db = _session()
    delivery, _endpoint = _delivery(db)
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500)))

    webhook_dispatch.deliver_one(db, delivery, client=client)
    db.commit()
    assert delivery.status == "pending" and delivery.attempts == 1
    assert delivery.next_retry_at is not None       # retried later, not dropped
    assert "HTTP 500" in delivery.last_error

    delivery.next_retry_at = None
    webhook_dispatch.deliver_one(db, delivery, client=client)
    webhook_dispatch.deliver_one(db, delivery, client=client)
    db.commit()
    assert delivery.attempts == 3 and delivery.status == "failed"  # max_attempts reached


def test_delivery_waiting_for_its_backoff_is_skipped():
    db = _session()
    delivery, _endpoint = _delivery(db)
    delivery.next_retry_at = datetime(2099, 1, 1, tzinfo=timezone.utc)
    db.commit()

    def explode(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("must not be called before the backoff elapses")

    summary = webhook_dispatch.dispatch_pending(db, client=httpx.Client(transport=httpx.MockTransport(explode)))
    assert summary["skipped"] == 1 and summary["delivered"] == 0
