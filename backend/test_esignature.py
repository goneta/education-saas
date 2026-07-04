import uuid

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import self_documents
from backend.services import esignature


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.commit()
    return school


def _family(db, school):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    profile = models.StudentProfile(user_id=user.id, registration_number=f"R{tag}")
    db.add(profile); db.flush()
    parent = models.User(email=f"par_{tag}@example.com", hashed_password="x", full_name=f"Parent {tag}", role=models.UserRole.PARENT, school_id=school.id, is_active=True)
    db.add(parent); db.flush()
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=profile.id, is_active=True))
    db.commit()
    return user, profile, parent


def _document(db, school, profile):
    user = db.query(models.User).filter(models.User.id == profile.user_id).one()
    doc = self_documents.generate_certificate(student_id=None, db=db, current_user=user)
    return db.query(models.GeneratedDocument).filter(models.GeneratedDocument.reference == doc["reference"]).one()


def test_sign_and_verify_valid_signature():
    db = _session()
    school = _school(db)
    user, profile, parent = _family(db, school)
    document = _document(db, school, profile)

    info = self_documents.sign_document(document_id=document.id, db=db, current_user=parent)
    assert info["valid"] is True and info["authentic"] is True and info["tampered"] is False
    assert info["signer_name"] == parent.full_name and len(info["code"]) == 14  # XXXX-XXXX-XXXX

    verified = self_documents.verify_document(reference=document.reference, db=db, current_user=user)
    assert verified["valid"] is True
    assert len(verified["signatures"]) == 1 and verified["signatures"][0]["valid"] is True

    mine = self_documents.my_documents(student_id=None, limit=50, db=db, current_user=user)
    assert mine[0]["signatures"][0]["signer_name"] == parent.full_name


def test_tampering_is_detected():
    db = _session()
    school = _school(db)
    user, profile, parent = _family(db, school)
    document = _document(db, school, profile)
    self_documents.sign_document(document_id=document.id, db=db, current_user=parent)

    # Mutate the document AFTER signing: authenticity holds, integrity fails.
    document.content = {**(document.content or {}), "student": {"full_name": "Falsifié"}}
    db.commit()

    row = db.query(models.DocumentSignature).one()
    checks = esignature.verify_signature(document, row)
    assert checks["authentic"] is True and checks["tampered"] is True and checks["valid"] is False

    # A forged signature value fails authenticity.
    row.signature = "0" * 64
    db.commit()
    forged = esignature.verify_signature(document, row)
    assert forged["authentic"] is False and forged["valid"] is False


def test_sign_guards():
    db = _session()
    school = _school(db)
    user, profile, parent = _family(db, school)
    document = _document(db, school, profile)

    # Student signs their own document; a second signature by the same signer -> 409.
    self_documents.sign_document(document_id=document.id, db=db, current_user=user)
    try:
        self_documents.sign_document(document_id=document.id, db=db, current_user=user)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 409

    # Parent AND student can both sign (two distinct signatures).
    self_documents.sign_document(document_id=document.id, db=db, current_user=parent)
    assert db.query(models.DocumentSignature).count() == 2

    # An unlinked user cannot sign.
    _other_user, _other_profile, other_parent = _family(db, school)
    try:
        self_documents.sign_document(document_id=document.id, db=db, current_user=other_parent)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403

    # Unknown document -> 404.
    try:
        self_documents.sign_document(document_id=999999, db=db, current_user=user)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404
