import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import sis


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_user(db, role=models.UserRole.SCHOOL_ADMIN):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"S {uid}", domain_prefix=f"s_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    user = models.User(email=f"a_{uid}@s.local", hashed_password="x", full_name="Admin", role=role, school_id=school.id, is_active=True)
    db.add(user)
    db.commit()
    return school, user


def _student(db, school):
    u = models.User(email=f"st_{uuid.uuid4().hex[:6]}@s.local", hashed_password="x", full_name="Stud", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(u)
    db.flush()
    p = models.StudentProfile(user_id=u.id, registration_number=f"R{uuid.uuid4().hex[:4]}")
    db.add(p)
    db.commit()
    return p


def test_guardians_and_emergency_contacts():
    db = _session()
    school, admin = _school_user(db)
    student = _student(db, school)
    sis.add_guardian(student.id, schemas.GuardianCreate(full_name="Mère", relationship_type="mother", is_primary=True), db=db, current_user=admin)
    sis.add_guardian(student.id, schemas.GuardianCreate(full_name="Père", relationship_type="father"), db=db, current_user=admin)
    guardians = sis.list_guardians(student.id, db=db, current_user=admin)
    assert len(guardians) == 2 and guardians[0].is_primary  # primary first
    sis.add_emergency_contact(student.id, schemas.EmergencyContactCreate(full_name="Oncle", phone="123", priority=1), db=db, current_user=admin)
    assert len(sis.list_emergency_contacts(student.id, db=db, current_user=admin)) == 1


def test_medical_record_upsert_and_restricted():
    db = _session()
    school, admin = _school_user(db)
    student = _student(db, school)
    sis.upsert_medical_record(student.id, schemas.MedicalRecordUpsert(blood_group="O+", allergies="Pollen"), db=db, current_user=admin)
    rec = sis.get_medical_record(student.id, db=db, current_user=admin)
    assert rec.blood_group == "O+" and rec.allergies == "Pollen"
    # Upsert again updates, not duplicates.
    sis.upsert_medical_record(student.id, schemas.MedicalRecordUpsert(allergies="None"), db=db, current_user=admin)
    assert db.query(models.StudentMedicalRecord).filter(models.StudentMedicalRecord.student_id == student.id).count() == 1
    # A teacher cannot read medical data.
    teacher = models.User(email=f"t_{uuid.uuid4().hex[:6]}@s.local", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(teacher); db.commit()
    try:
        sis.get_medical_record(student.id, db=db, current_user=teacher)
        assert False, "teacher must not read medical records"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403


def test_cross_school_student_blocked():
    db = _session()
    school_a, admin_a = _school_user(db)
    school_b, _ = _school_user(db)
    foreign = _student(db, school_b)
    try:
        sis.add_guardian(foreign.id, schemas.GuardianCreate(full_name="X"), db=db, current_user=admin_a)
        assert False, "cross-school student should be rejected"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 404


def test_guardian_write_requires_admin():
    db = _session()
    school, _ = _school_user(db)
    student = _student(db, school)
    weak = models.User(email=f"w_{uuid.uuid4().hex[:6]}@s.local", hashed_password="x", full_name="W", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(weak); db.commit()
    try:
        sis.add_guardian(student.id, schemas.GuardianCreate(full_name="X"), db=db, current_user=weak)
        assert False, "student must not add guardians"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
