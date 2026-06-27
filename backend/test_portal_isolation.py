from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import documents


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _student(db, school, suffix):
    user = models.User(
        email=f"student_{suffix}@portal.test",
        hashed_password="x",
        full_name=f"Student {suffix}",
        role=models.UserRole.STUDENT,
        school=school,
        is_active=True,
    )
    db.add(user)
    db.flush()
    profile = models.StudentProfile(
        user_id=user.id,
        registration_number=f"MAT{suffix}",
        parent_name="P",
        parent_phone="",
    )
    db.add(profile)
    db.flush()
    doc = models.GeneratedDocument(
        document_type=models.GeneratedDocumentType.REPORT_CARD,
        title=f"Bulletin {suffix}",
        student_id=profile.id,
        school_id=school.id,
    )
    db.add(doc)
    db.flush()
    return profile, doc


def _fixtures(db):
    school = models.School(name="Portal School", domain_prefix="portal", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    child_a, doc_a = _student(db, school, "A")
    child_b, doc_b = _student(db, school, "B")
    parent = models.User(
        email="parent@portal.test",
        hashed_password="x",
        full_name="Parent",
        role=models.UserRole.PARENT,
        school=school,
        is_active=True,
    )
    db.add(parent)
    db.flush()
    db.commit()
    return school, child_a, doc_a, child_b, doc_b, parent


def test_unlinked_parent_sees_no_documents():
    db = _session()
    _school, _child_a, _doc_a, _child_b, _doc_b, parent = _fixtures(db)
    # Parent has no ParentStudentLink rows: must see nothing, not the whole school.
    result = documents.portal_documents(db=db, current_user=parent)
    assert result["documents"] == []


def test_linked_parent_sees_only_their_child():
    db = _session()
    _school, child_a, doc_a, _child_b, doc_b, parent = _fixtures(db)
    db.add(models.ParentStudentLink(parent_user_id=parent.id, student_id=child_a.id, relation="parent"))
    db.commit()
    result = documents.portal_documents(db=db, current_user=parent)
    ids = {row["id"] for row in result["documents"]}
    assert doc_a.id in ids
    assert doc_b.id not in ids


def test_unlinked_parent_cannot_target_other_student_by_id():
    db = _session()
    import pytest
    from fastapi import HTTPException

    _school, child_a, _doc_a, _child_b, _doc_b, parent = _fixtures(db)
    with pytest.raises(HTTPException) as exc:
        documents.portal_documents(student_id=child_a.id, db=db, current_user=parent)
    assert exc.value.status_code == 403
