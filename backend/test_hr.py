import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import hr


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"H {uid}", domain_prefix=f"h_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{uid}@h.local", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    teacher = models.User(email=f"t_{uid}@h.local", hashed_password="x", full_name="Teach", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add_all([admin, teacher]); db.commit()
    return school, admin, teacher


def test_leave_request_lifecycle_and_notification():
    db = _session()
    school, admin, teacher = _school(db)
    req = hr.create_leave_request(schemas.LeaveSelfRequestCreate(leave_type="sick", start_date=datetime(2026, 9, 1), end_date=datetime(2026, 9, 3), reason="Flu"), db=db, current_user=teacher)
    assert req.status == models.LeaveStatus.PENDING and req.staff_user_id == teacher.id
    decided = hr.decide_leave_request(req.id, schemas.LeaveDecision(status="approved"), db=db, current_user=admin)
    assert decided.status == models.LeaveStatus.APPROVED and decided.decided_by_id == admin.id
    assert db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "hr.leave_decided").count() == 1


def test_staff_sees_only_own_admin_sees_all():
    db = _session()
    school, admin, teacher = _school(db)
    other = models.User(email=f"o_{uuid.uuid4().hex[:5]}@h.local", hashed_password="x", full_name="O", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(other); db.commit()
    hr.create_leave_request(schemas.LeaveSelfRequestCreate(start_date=datetime(2026, 9, 1), end_date=datetime(2026, 9, 2)), db=db, current_user=teacher)
    hr.create_leave_request(schemas.LeaveSelfRequestCreate(start_date=datetime(2026, 9, 1), end_date=datetime(2026, 9, 2)), db=db, current_user=other)
    assert len(hr.list_leave_requests(db=db, current_user=teacher)) == 1  # own only
    assert len(hr.list_leave_requests(db=db, current_user=admin)) == 2    # all


def test_non_admin_cannot_decide_and_bad_dates_rejected():
    db = _session()
    school, admin, teacher = _school(db)
    req = hr.create_leave_request(schemas.LeaveSelfRequestCreate(start_date=datetime(2026, 9, 1), end_date=datetime(2026, 9, 2)), db=db, current_user=teacher)
    try:
        hr.decide_leave_request(req.id, schemas.LeaveDecision(status="approved"), db=db, current_user=teacher)
        assert False, "teacher cannot approve"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
    try:
        hr.create_leave_request(schemas.LeaveSelfRequestCreate(start_date=datetime(2026, 9, 5), end_date=datetime(2026, 9, 1)), db=db, current_user=teacher)
        assert False, "end before start should be rejected"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
