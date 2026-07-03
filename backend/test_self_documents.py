import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import self_documents


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.commit()
    return school


def _student(db, school):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"R{tag}")
    db.add(profile); db.commit()
    return user, profile


def _parent(db, school, profile):
    tag = uuid.uuid4().hex[:5]
    parent = models.User(email=f"par_{tag}@example.com", hashed_password="x", full_name="Parent", role=models.UserRole.PARENT, school_id=school.id, is_active=True)
    db.add(parent); db.flush()
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=profile.id))
    db.commit()
    return parent


def _paid_fee(db, school, profile, amount=10000, paid=10000):
    fee = models.Fee(
        title=f"Scolarité {uuid.uuid4().hex[:4]}", amount=amount,
        due_date=datetime.now(timezone.utc), status=models.FeeStatus.PAID,
        student_id=profile.id, school_id=school.id,
    )
    db.add(fee); db.flush()
    payment = models.Payment(fee_id=fee.id, amount=paid, status="successful", receipt_number=f"RC-{uuid.uuid4().hex[:6]}")
    db.add(payment); db.commit()
    return fee, payment


def test_student_generates_certificate_and_attestation():
    db = _session()
    school = _school(db)
    user, profile = _student(db, school)

    cert = self_documents.generate_certificate(student_id=None, db=db, current_user=user)
    att = self_documents.generate_attestation(student_id=None, db=db, current_user=user)

    assert cert["reference"].startswith("CERT-") and cert["doc_type"] == "certificate"
    assert att["reference"].startswith("ATT-") and att["doc_type"] == "attestation"
    assert cert["student"]["full_name"] == user.full_name
    assert cert["school"]["name"] == school.name

    rows = db.query(models.GeneratedDocument).filter(models.GeneratedDocument.source_type == "self_service").all()
    assert len(rows) == 2
    assert {r.document_type for r in rows} == {models.GeneratedDocumentType.CERTIFICATE, models.GeneratedDocumentType.OTHER}
    assert all(r.student_id == profile.id and r.school_id == school.id for r in rows)


def test_parent_generates_for_linked_child_only():
    db = _session()
    school = _school(db)
    _user, profile = _student(db, school)
    _other_user, other_profile = _student(db, school)
    parent = _parent(db, school, profile)

    doc = self_documents.generate_certificate(student_id=profile.id, db=db, current_user=parent)
    assert doc["student"]["registration_number"] == profile.registration_number
    stored = db.query(models.GeneratedDocument).filter(models.GeneratedDocument.reference == doc["reference"]).first()
    assert stored.parent_user_id == parent.id

    try:
        self_documents.generate_certificate(student_id=other_profile.id, db=db, current_user=parent)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403


def test_receipt_lists_and_generates_own_payments_only():
    db = _session()
    school = _school(db)
    user, profile = _student(db, school)
    other_user, other_profile = _student(db, school)
    _fee, payment = _paid_fee(db, school, profile)
    _other_fee, other_payment = _paid_fee(db, school, other_profile)

    payments = self_documents.my_payments(student_id=None, db=db, current_user=user)
    assert [p["payment_id"] for p in payments] == [payment.id]

    receipt = self_documents.generate_receipt(payment_id=payment.id, student_id=None, db=db, current_user=user)
    assert receipt["payment"]["receipt_number"] == payment.receipt_number
    assert receipt["payment"]["outstanding_after"] == 0
    stored = db.query(models.GeneratedDocument).filter(models.GeneratedDocument.reference == receipt["reference"]).first()
    assert stored.document_type == models.GeneratedDocumentType.RECEIPT and stored.source_id == payment.id

    try:
        self_documents.generate_receipt(payment_id=other_payment.id, student_id=None, db=db, current_user=user)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404


def test_mine_and_verify():
    db = _session()
    school = _school(db)
    user, _profile = _student(db, school)
    doc = self_documents.generate_certificate(student_id=None, db=db, current_user=user)

    mine = self_documents.my_documents(student_id=None, limit=50, db=db, current_user=user)
    assert len(mine) == 1 and mine[0]["reference"] == doc["reference"] and mine[0]["doc_type"] == "certificate"

    ok = self_documents.verify_document(reference=doc["reference"], db=db, current_user=user)
    assert ok["valid"] is True and ok["student_name"] == user.full_name and ok["school_name"] == school.name
    assert self_documents.verify_document(reference="CERT-DOESNOTEXIST", db=db, current_user=user)["valid"] is False


def test_children_listing():
    db = _session()
    school = _school(db)
    user, profile = _student(db, school)
    _other_user, _other_profile = _student(db, school)
    parent = _parent(db, school, profile)

    as_student = self_documents.my_children(db=db, current_user=user)
    assert [c["student_id"] for c in as_student] == [profile.id]

    as_parent = self_documents.my_children(db=db, current_user=parent)
    assert [c["student_id"] for c in as_parent] == [profile.id]
    assert as_parent[0]["full_name"] == user.full_name


def test_teacher_denied_and_admin_needs_student_id():
    db = _session()
    school = _school(db)
    _user, profile = _student(db, school)
    teacher = models.User(email=f"t_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    admin = models.User(email=f"a_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="A", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add_all([teacher, admin]); db.commit()

    try:
        self_documents.generate_certificate(student_id=profile.id, db=db, current_user=teacher)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403

    try:
        self_documents.generate_certificate(student_id=None, db=db, current_user=admin)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 400

    doc = self_documents.generate_certificate(student_id=profile.id, db=db, current_user=admin)
    assert doc["reference"].startswith("CERT-")


def test_admin_cannot_generate_for_other_school_student():
    db = _session()
    school_a = _school(db)
    school_b = _school(db)
    _user, profile_b = _student(db, school_b)
    admin_a = models.User(email=f"a_{uuid.uuid4().hex[:5]}@example.com", hashed_password="x", full_name="A", role=models.UserRole.SCHOOL_ADMIN, school_id=school_a.id, is_active=True)
    db.add(admin_a); db.commit()

    try:
        self_documents.generate_certificate(student_id=profile_b.id, db=db, current_user=admin_a)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404
