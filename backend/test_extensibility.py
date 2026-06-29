import hashlib
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import extensibility


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"E {uid}", domain_prefix=f"e_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{uid}@e.local", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    return school, admin


def test_emit_event_matches_subscriptions():
    db = _session()
    school, admin = _school(db)
    # One endpoint subscribed to a specific event, one catch-all, one for another event.
    extensibility.create_webhook(schemas.WebhookEndpointCreate(url="https://a.test", event_types=["student.created"]), db=db, current_user=admin)
    extensibility.create_webhook(schemas.WebhookEndpointCreate(url="https://b.test", event_types=None), db=db, current_user=admin)
    extensibility.create_webhook(schemas.WebhookEndpointCreate(url="https://c.test", event_types=["fee.paid"]), db=db, current_user=admin)
    queued = extensibility.emit_event(db, school.id, "student.created", {"id": 1})
    db.commit()
    assert queued == 2  # specific + catch-all, not the fee.paid one
    deliveries = db.query(models.WebhookDelivery).filter(models.WebhookDelivery.event_type == "student.created").all()
    assert len(deliveries) == 2 and all(d.status == "pending" for d in deliveries)


def test_emit_event_tenant_scoped():
    db = _session()
    school_a, admin_a = _school(db)
    school_b, admin_b = _school(db)
    extensibility.create_webhook(schemas.WebhookEndpointCreate(url="https://a.test"), db=db, current_user=admin_a)
    # Event in school B must not hit school A's endpoint.
    assert extensibility.emit_event(db, school_b.id, "x.y", {}) == 0


def test_api_key_returned_once_and_hashed():
    db = _session()
    school, admin = _school(db)
    created = extensibility.create_api_key(schemas.ApiKeyCreate(name="CI"), db=db, current_user=admin)
    raw = created["api_key"]
    assert raw.startswith("tk_")
    row = db.query(models.ApiKey).filter(models.ApiKey.id == created["id"]).first()
    # Stored hash matches the plaintext; plaintext itself is not stored.
    assert row.key_hash == hashlib.sha256(raw.encode()).hexdigest()
    assert row.prefix == raw[:10]
    # Revoke deactivates.
    extensibility.revoke_api_key(row.id, db=db, current_user=admin)
    db.refresh(row)
    assert row.is_active is False


def test_retry_respects_max_attempts_and_authz():
    db = _session()
    school, admin = _school(db)
    ep = extensibility.create_webhook(schemas.WebhookEndpointCreate(url="https://a.test"), db=db, current_user=admin)
    extensibility.emit_event(db, school.id, "e", {}); db.commit()
    delivery = db.query(models.WebhookDelivery).first()
    delivery.attempts = delivery.max_attempts
    delivery.status = "failed"
    db.commit()
    try:
        extensibility.retry_delivery(delivery.id, db=db, current_user=admin)
        assert False, "exhausted retries should 409"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 409
    # Non-admin cannot manage webhooks.
    student = models.User(email=f"s_{uuid.uuid4().hex[:5]}@e.local", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student); db.commit()
    try:
        extensibility.list_webhooks(db=db, current_user=student)
        assert False, "student cannot list webhooks"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
