import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import levels


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _user(db, role):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"L {uid}", domain_prefix=f"lv_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    user = models.User(email=f"u_{uid}@lv.local", hashed_password="x", full_name="U", role=role, school_id=school.id, is_active=True)
    db.add(user); db.commit()
    return school, user


def test_super_admin_crud_and_read_open():
    db = _session()
    _s, sa = _user(db, models.UserRole.SUPER_ADMIN)
    _s2, admin = _user(db, models.UserRole.SCHOOL_ADMIN)
    lvl = levels.create_level(schemas.SchoolLevelCreate(code="CP1", name="Cours Préparatoire 1", category="primaire", sort_order=1), db=db, current_user=sa)
    assert lvl.code == "CP1"
    # School admin can READ (needed to create classes) but not write.
    assert len(levels.list_levels(db=db, current_user=admin)) == 1
    try:
        levels.create_level(schemas.SchoolLevelCreate(code="CP2", name="x"), db=db, current_user=admin)
        assert False, "non super-admin must not create levels"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
    # Update + toggle.
    levels.update_level(lvl.id, schemas.SchoolLevelUpdate(is_active=False), db=db, current_user=sa)
    assert levels.list_levels(active_only=True, db=db, current_user=admin) == []


def test_duplicate_code_rejected():
    db = _session()
    _s, sa = _user(db, models.UserRole.SUPER_ADMIN)
    levels.create_level(schemas.SchoolLevelCreate(code="6EME", name="Sixième"), db=db, current_user=sa)
    try:
        levels.create_level(schemas.SchoolLevelCreate(code="6EME", name="dup"), db=db, current_user=sa)
        assert False, "duplicate code should 409"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 409


def test_delete_blocked_when_used_by_class():
    db = _session()
    school, sa = _user(db, models.UserRole.SUPER_ADMIN)
    lvl = levels.create_level(schemas.SchoolLevelCreate(code="CM2", name="Cours Moyen 2"), db=db, current_user=sa)
    # A class referencing the level code.
    db.add(models.Class(name="CM2 A", level="CM2", school_id=school.id)); db.commit()
    try:
        levels.delete_level(lvl.id, db=db, current_user=sa)
        assert False, "used level should not be deletable"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 409
    # Unused level deletes fine.
    free = levels.create_level(schemas.SchoolLevelCreate(code="TLE", name="Terminale"), db=db, current_user=sa)
    assert levels.delete_level(free.id, db=db, current_user=sa)["status"] == "deleted"
