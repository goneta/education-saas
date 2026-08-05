"""Lot 3 — audit DATA-01 : suppression de données référencées.

No `ON DELETE` rule exists in the schema, so deleting referenced master data
either raised an opaque 500 (PostgreSQL FK violation) or silently destroyed
dependent rows through an ORM cascade. The rule is now explicit: blocked with a
409 naming what stands in the way.
"""

import uuid
from datetime import datetime, time

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import deletion_guard


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(s); db.commit()
    return s


def _class(db, school):
    row = models.Class(name=f"6e {uuid.uuid4().hex[:4]}", level="6EME", school_id=school.id)
    db.add(row); db.commit()
    return row


def _subject(db, school):
    row = models.Subject(name=f"Maths {uuid.uuid4().hex[:4]}", code=f"M{uuid.uuid4().hex[:4]}", school_id=school.id)
    db.add(row); db.commit()
    return row


def test_free_class_and_subject_are_deletable():
    db = _session()
    school = _school(db)
    cls, subject = _class(db, school), _subject(db, school)
    deletion_guard.ensure_deletable(db, entity_label="cette classe",
                                    references=deletion_guard.CLASS_REFERENCES, value=cls.id)
    deletion_guard.ensure_deletable(db, entity_label="cette matière",
                                    references=deletion_guard.SUBJECT_REFERENCES, value=subject.id)


def test_class_referenced_by_a_timetable_slot_is_blocked():
    db = _session()
    school = _school(db)
    cls, subject = _class(db, school), _subject(db, school)
    db.add(models.Timetable(class_id=cls.id, subject_id=subject.id, day_of_week="monday",
                            start_time=time(8, 0), end_time=time(9, 0)))
    db.commit()

    with pytest.raises(HTTPException) as exc:
        deletion_guard.ensure_deletable(db, entity_label="cette classe",
                                        references=deletion_guard.CLASS_REFERENCES, value=cls.id)
    assert exc.value.status_code == 409
    # The message names the blocker and its count — actionable, not a 500.
    assert "cours à l'emploi du temps" in exc.value.detail
    assert "1" in exc.value.detail

    # The same slot also protects the subject (previously unguarded entirely).
    with pytest.raises(HTTPException) as exc2:
        deletion_guard.ensure_deletable(db, entity_label="cette matière",
                                        references=deletion_guard.SUBJECT_REFERENCES, value=subject.id)
    assert exc2.value.status_code == 409


def test_all_declared_class_dependencies_are_detected():
    db = _session()
    school = _school(db)
    cls = _class(db, school)
    user = models.User(email=f"s_{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", full_name="E",
                       role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(user); db.flush()
    db.add(models.StudentProfile(user_id=user.id, registration_number=f"MAT-{uuid.uuid4().hex[:6]}",
                                 current_class_id=cls.id))
    db.add(models.Assignment(title="Devoir", class_id=cls.id, school_id=school.id))
    db.add(models.SchoolActivity(name="Sortie", class_id=cls.id, school_id=school.id))
    db.commit()

    blocking = dict(deletion_guard.blocking_references(db, deletion_guard.CLASS_REFERENCES, cls.id))
    assert blocking.get("élève(s) rattaché(s)") == 1
    assert blocking.get("devoir(s)") == 1
    assert blocking.get("activité(s)") == 1


def test_assessment_holding_grades_is_blocked():
    db = _session()
    school = _school(db)
    cls, subject = _class(db, school), _subject(db, school)
    term = models.Term(name="Trimestre 1")
    db.add(term); db.flush()
    assessment = models.Assessment(title="Compo 1", class_id=cls.id, subject_id=subject.id,
                                   term_id=term.id, date=datetime(2026, 6, 1), max_score=20)
    db.add(assessment); db.flush()
    student_user = models.User(email=f"s_{uuid.uuid4().hex[:6]}@x.com", hashed_password="x", full_name="E",
                               role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student_user); db.flush()
    profile = models.StudentProfile(user_id=student_user.id, registration_number=f"MAT-{uuid.uuid4().hex[:6]}")
    db.add(profile); db.flush()
    db.add(models.Grade(assessment_id=assessment.id, student_id=profile.id, score=15))
    db.commit()

    with pytest.raises(HTTPException) as exc:
        deletion_guard.ensure_deletable(db, entity_label="cette évaluation",
                                        references=deletion_guard.ASSESSMENT_REFERENCES, value=assessment.id)
    assert exc.value.status_code == 409
    assert "note(s) saisie(s)" in exc.value.detail
