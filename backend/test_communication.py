import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import communication


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_user(db, role=models.UserRole.SCHOOL_ADMIN):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"C {uid}", domain_prefix=f"c_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    user = models.User(email=f"a_{uid}@c.local", hashed_password="x", full_name="Admin", role=role, school_id=school.id, is_active=True)
    db.add(user); db.commit()
    return school, user


def test_create_and_publish_fans_out_to_audience():
    db = _session()
    school, admin = _school_user(db)
    # Two teachers + one parent in the school.
    for i in range(2):
        db.add(models.User(email=f"t{i}_{uuid.uuid4().hex[:5]}@c.local", hashed_password="x", full_name=f"T{i}", role=models.UserRole.TEACHER, school_id=school.id, is_active=True))
    db.add(models.User(email=f"p_{uuid.uuid4().hex[:5]}@c.local", hashed_password="x", full_name="P", role=models.UserRole.PARENT, school_id=school.id, is_active=True))
    db.commit()

    ann = communication.create_announcement(schemas.AnnouncementCreate(title="Réunion", body="Demain 9h", audience="teachers"), db=db, current_user=admin)
    assert ann.status == "draft"
    published = communication.publish_announcement(ann.id, db=db, current_user=admin)
    assert published.status == "published" and published.published_at is not None
    # Notifications went to the 2 teachers (audience filter), not the parent.
    notifs = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "announcement.published").all()
    assert len(notifs) == 2


def test_scheduled_status_and_publish_idempotent():
    db = _session()
    school, admin = _school_user(db)
    from datetime import datetime, timezone
    ann = communication.create_announcement(
        schemas.AnnouncementCreate(title="Plus tard", body="...", scheduled_for=datetime(2030, 1, 1, tzinfo=timezone.utc)),
        db=db, current_user=admin,
    )
    assert ann.status == "scheduled"
    communication.publish_announcement(ann.id, db=db, current_user=admin)
    first = db.query(models.NotificationHistory).count()
    communication.publish_announcement(ann.id, db=db, current_user=admin)  # idempotent
    assert db.query(models.NotificationHistory).count() == first


def test_non_publisher_blocked_and_tenant_isolation():
    db = _session()
    school, admin = _school_user(db)
    student = models.User(email=f"s_{uuid.uuid4().hex[:5]}@c.local", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student); db.commit()
    try:
        communication.create_announcement(schemas.AnnouncementCreate(title="X", body="Y"), db=db, current_user=student)
        assert False, "student must not create announcements"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
    # Other school cannot see/publish.
    ann = communication.create_announcement(schemas.AnnouncementCreate(title="A", body="B"), db=db, current_user=admin)
    _school_b, admin_b = _school_user(db)
    assert len(communication.list_announcements(db=db, current_user=admin_b)) == 0
    try:
        communication.publish_announcement(ann.id, db=db, current_user=admin_b)
        assert False, "cross-school publish should 404"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 404
