import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import communication, extensibility, public_api


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_with_admin(db, tag):
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{tag}@example.com", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    return school, admin


def _mint_key(db, admin):
    created = extensibility.create_api_key(payload=schemas.ApiKeyCreate(name="partner"), db=db, current_user=admin)
    return created["api_key"]


def test_api_key_auth_valid_invalid_revoked():
    db = _session()
    _school, admin = _school_with_admin(db, uuid.uuid4().hex[:6])
    raw = _mint_key(db, admin)
    row = public_api.require_api_key(x_api_key=raw, db=db)
    assert row.school_id == admin.school_id and row.last_used_at is not None
    # Unknown key -> 401
    for bad in [None, "tk_definitely_wrong"]:
        try:
            public_api.require_api_key(x_api_key=bad, db=db)
            assert False, "should have raised"
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 401
    # Revoked key -> 401
    extensibility.revoke_api_key(key_id=row.id, db=db, current_user=admin)
    try:
        public_api.require_api_key(x_api_key=raw, db=db)
        assert False
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 401


def test_public_endpoints_are_tenant_scoped():
    db = _session()
    tag_a, tag_b = uuid.uuid4().hex[:6], uuid.uuid4().hex[:6]
    school_a, admin_a = _school_with_admin(db, tag_a)
    school_b, _admin_b = _school_with_admin(db, tag_b)
    # One student in each school.
    for school, tag in [(school_a, tag_a), (school_b, tag_b)]:
        user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
        db.add(user); db.flush()
        db.add(models.StudentProfile(user_id=user.id, registration_number=f"R{tag}"))
    db.add(models.Class(name="6A", level="6E", school_id=school_a.id))
    db.commit()

    raw = _mint_key(db, admin_a)
    key = public_api.require_api_key(x_api_key=raw, db=db)
    students = public_api.list_students(limit=50, offset=0, api_key=key, db=db)
    assert len(students) == 1 and students[0].registration_number == f"R{tag_a}"
    classes = public_api.list_classes(limit=100, offset=0, api_key=key, db=db)
    assert [c.name for c in classes] == ["6A"]
    info = public_api.key_info(api_key=key, db=db)
    assert info.school_id == school_a.id and info.key_prefix == raw[:10]


def test_announcement_publish_emits_webhook_delivery():
    db = _session()
    _school, admin = _school_with_admin(db, uuid.uuid4().hex[:6])
    # Endpoint subscribed to announcement.published; another subscribed elsewhere.
    extensibility.create_webhook(payload=schemas.WebhookEndpointCreate(url="https://partner.example/hook", event_types=["announcement.published"]), db=db, current_user=admin)
    extensibility.create_webhook(payload=schemas.WebhookEndpointCreate(url="https://other.example/hook", event_types=["payment.recorded"]), db=db, current_user=admin)
    ann = models.Announcement(school_id=admin.school_id, title="Rentrée", body="Lundi 8h", audience="all", is_emergency=False, status="draft")
    db.add(ann); db.commit()

    communication.publish_announcement(announcement_id=ann.id, db=db, current_user=admin)

    deliveries = extensibility.list_deliveries(status=None, limit=50, db=db, current_user=admin)
    assert len(deliveries) == 1
    assert deliveries[0].event_type == "announcement.published" and deliveries[0].status == "pending"


def test_emit_event_catch_all_endpoint():
    db = _session()
    _school, admin = _school_with_admin(db, uuid.uuid4().hex[:6])
    # No event_types -> receives everything.
    extensibility.create_webhook(payload=schemas.WebhookEndpointCreate(url="https://all.example/hook"), db=db, current_user=admin)
    queued = extensibility.emit_event(db, admin.school_id, "custom.event", {"x": 1})
    db.commit()
    assert queued == 1
    rows = extensibility.list_deliveries(status="pending", limit=10, db=db, current_user=admin)
    assert rows and rows[0].event_type == "custom.event"
