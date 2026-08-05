"""The student list must never silently hide a school's own students.

Root-cause coverage for the "Gestion → Élèves affiche une liste vide" bug:
profiles pinned to a school-model assignment that is no longer active for the
school (the assignment was replaced or deactivated) used to be excluded by the
context filter — the tolerant read now treats such stale pins like unpinned
profiles. Self-contained in-memory DB (no dev database required).
"""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers.students import list_students, list_students_diagnostics


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _setup_school(db):
    tag = uuid.uuid4().hex[:6]
    org = models.Organization(name=f"Org {tag}")
    db.add(org); db.flush()
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}",
                           school_type=models.SchoolType.GENERAL, organization_id=org.id)
    db.add(school); db.flush()
    model_old = models.SchoolModel(code=f"OLD-{tag}", name="Ancien modèle")
    model_new = models.SchoolModel(code=f"NEW-{tag}", name="Modèle actuel")
    db.add_all([model_old, model_new]); db.flush()
    sma_old = models.SchoolModelAssignment(school_id=school.id, school_model_id=model_old.id, is_active=False)
    sma_new = models.SchoolModelAssignment(school_id=school.id, school_model_id=model_new.id, is_active=True)
    db.add_all([sma_old, sma_new]); db.commit()
    return school, sma_old, sma_new


def _student(db, school, sma_id, label):
    tag = uuid.uuid4().hex[:6]
    user = models.User(email=f"{label}_{tag}@x.com", hashed_password="x", full_name=f"Élève {label}",
                       role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"MAT-{label}-{tag}",
                                    school_model_assignment_id=sma_id)
    db.add(profile); db.commit()
    return user


def _admin(db, school):
    tag = uuid.uuid4().hex[:6]
    admin = models.User(email=f"admin_{tag}@x.com", hashed_password="x", full_name="Admin",
                        role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(admin); db.commit()
    return admin


def test_students_with_stale_model_pin_stay_visible():
    """Profiles pinned to an inactive/replaced assignment, pinned to the active
    one, or unpinned must ALL appear for the school's active context."""
    db = _session()
    school, sma_old, sma_new = _setup_school(db)
    admin = _admin(db, school)
    stale = _student(db, school, sma_old.id, "stale")     # pinned to the DEACTIVATED assignment
    current = _student(db, school, sma_new.id, "current") # pinned to the active assignment
    unpinned = _student(db, school, None, "unpinned")     # legacy, never pinned

    rows = list_students(skip=0, limit=100, class_id=None, school_id=None, search=None,
                         current_user=admin, db=db)
    ids = {row.id for row in rows}
    assert current.id in ids
    assert unpinned.id in ids
    assert stale.id in ids  # the bug: this one used to disappear

    # Other schools' students never leak in.
    other_school, _, other_sma = _setup_school(db)
    foreign = _student(db, other_school, other_sma.id, "foreign")
    rows = list_students(skip=0, limit=100, class_id=None, school_id=None, search=None,
                         current_user=admin, db=db)
    assert foreign.id not in {row.id for row in rows}


def test_diagnostics_explains_empty_list():
    """The diagnostics endpoint mirrors the list filters and yields hints."""
    db = _session()
    school, _, _ = _setup_school(db)
    admin = _admin(db, school)
    out = list_students_diagnostics(current_user=admin, db=db)
    assert out["stages"]["student_profiles_total"] == 0
    assert out["stages"]["final_list_count"] == 0
    assert out["hints"]  # explains that no student profile exists yet

    _student(db, school, None, "one")
    out = list_students_diagnostics(current_user=admin, db=db)
    assert out["stages"]["final_list_count"] == 1
