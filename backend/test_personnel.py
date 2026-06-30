import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import personnel


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _admin(db):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"S {uid}", domain_prefix=f"s_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{uid}@example.com", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    return school, admin


def test_create_staff_autocreates_user():
    db = _session()
    school, admin = _admin(db)
    payload = schemas.StaffCreate(full_name="Awa Diop", email="awa@example.com", primary_role="secretary", additional_roles=["cashier"], job_title="Secrétaire", status="active")
    out = personnel.create_staff(payload=payload, school_id=None, db=db, current_user=admin)
    assert out.user_id and out.primary_role == "secretary" and out.additional_roles == ["cashier"]
    assert out.generated_password  # auto-generated since no password given
    # A real, active user account exists.
    user = db.query(models.User).filter(models.User.id == out.user_id).first()
    assert user.is_active and user.role == models.UserRole.SECRETARY and user.school_id == school.id
    # Listing returns it.
    assert any(s.user_id == out.user_id for s in personnel.list_staff(school_id=None, db=db, current_user=admin))


def test_duplicate_email_and_bad_role_rejected():
    db = _session()
    _school, admin = _admin(db)
    personnel.create_staff(payload=schemas.StaffCreate(full_name="A", email="dup@example.com", primary_role="staff"), school_id=None, db=db, current_user=admin)
    for payload, code in [
        (schemas.StaffCreate(full_name="B", email="dup@example.com", primary_role="staff"), 409),
        (schemas.StaffCreate(full_name="C", email="c@example.com", primary_role="wizard"), 422),
    ]:
        try:
            personnel.create_staff(payload=payload, school_id=None, db=db, current_user=admin)
            assert False, "should have raised"
        except Exception as exc:
            assert getattr(exc, "status_code", None) == code


def test_update_status_and_deactivate_on_delete():
    db = _session()
    _school, admin = _admin(db)
    created = personnel.create_staff(payload=schemas.StaffCreate(full_name="D", email="d@example.com", primary_role="teacher"), school_id=None, db=db, current_user=admin)
    updated = personnel.update_staff(staff_id=created.id, payload=schemas.StaffUpdate(status="suspended", job_title="Prof principal"), school_id=None, db=db, current_user=admin)
    assert updated.status == "suspended" and updated.job_title == "Prof principal"
    personnel.delete_staff(staff_id=created.id, school_id=None, db=db, current_user=admin)
    user = db.query(models.User).filter(models.User.id == created.user_id).first()
    assert user.is_active is False
    assert db.query(models.StaffProfile).filter(models.StaffProfile.id == created.id).first() is None


def test_non_admin_forbidden():
    db = _session()
    _school, admin = _admin(db)
    teacher = models.User(email="t@example.com", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school_id=admin.school_id, is_active=True)
    db.add(teacher); db.commit()
    try:
        personnel.list_staff(school_id=None, db=db, current_user=teacher)
        assert False
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403


def test_staff_creation_records_initial_assignment():
    db = _session()
    school, admin = _admin(db)
    created = personnel.create_staff(payload=schemas.StaffCreate(full_name="Awa", email="awa2@example.com", primary_role="secretary"), school_id=None, db=db, current_user=admin)
    history = personnel.list_staff_assignments(staff_id=created.id, school_id=None, db=db, current_user=admin)
    assert len(history) == 1
    assert history[0].school_id == school.id and history[0].is_active and history[0].role == "secretary"


def test_add_and_end_assignment_across_establishments():
    db = _session()
    school_a, admin = _admin(db)
    # Super admin can post the staff member to a second establishment (historised).
    school_b = models.School(name="B", domain_prefix=f"b_{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL)
    db.add(school_b); db.flush()
    superadmin = models.User(email=f"su_{uuid.uuid4().hex[:6]}@example.com", hashed_password="x", full_name="SU", role=models.UserRole.SUPER_ADMIN, is_active=True)
    db.add(superadmin); db.commit()
    created = personnel.create_staff(payload=schemas.StaffCreate(full_name="Bob", email="bob@example.com", primary_role="staff"), school_id=None, db=db, current_user=admin)

    # School-admin of A cannot cross-assign to B.
    try:
        personnel.add_staff_assignment(staff_id=created.id, payload=schemas.StaffAssignmentCreate(school_id=school_b.id), school_id=None, db=db, current_user=admin)
        assert False, "school admin should not cross-assign"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403

    # Super admin can.
    posting = personnel.add_staff_assignment(staff_id=created.id, payload=schemas.StaffAssignmentCreate(school_id=school_b.id), school_id=school_a.id, db=db, current_user=superadmin)
    assert posting.school_id == school_b.id and posting.is_active
    history = personnel.list_staff_assignments(staff_id=created.id, school_id=None, db=db, current_user=admin)
    assert len(history) == 2  # A (initial) + B
    # Closing a posting keeps it in history but deactivates it.
    ended = personnel.end_staff_assignment(membership_id=posting.id, school_id=school_a.id, db=db, current_user=superadmin)
    assert ended.is_active is False and ended.end_date is not None and ended.membership_status == "ended"


def test_duplicate_active_assignment_rejected():
    db = _session()
    school_a, admin = _admin(db)
    created = personnel.create_staff(payload=schemas.StaffCreate(full_name="Cara", email="cara@example.com", primary_role="staff"), school_id=None, db=db, current_user=admin)
    # Re-posting to the same (already active) establishment is rejected.
    try:
        personnel.add_staff_assignment(staff_id=created.id, payload=schemas.StaffAssignmentCreate(school_id=school_a.id), school_id=None, db=db, current_user=admin)
        assert False
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 409
