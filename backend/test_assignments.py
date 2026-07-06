import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import assignments as R
from backend.services import ai_credits, assignments as svc
from backend.services.ai_service import ai_service


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    school = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.commit()
    return school


def _teacher(db, school, credits=1000):
    tag = uuid.uuid4().hex[:5]
    u = models.User(email=f"t_{tag}@x.com", hashed_password="x", full_name="Prof", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(u); db.commit()
    if credits:
        w = ai_credits.wallet_for_user(db, u); w.balance_credits = credits; db.commit()
    return u


def _class_subject(db, school):
    tag = uuid.uuid4().hex[:4]
    cls = models.Class(name=f"C{tag}", school_id=school.id); db.add(cls); db.flush()
    subject = models.Subject(name=f"Maths {tag}", school_id=school.id); db.add(subject); db.commit()
    return cls, subject


def _student(db, school, cls, parent=False):
    tag = uuid.uuid4().hex[:5]
    u = models.User(email=f"s_{tag}@x.com", hashed_password="x", full_name=f"Eleve {tag}", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(u); db.flush()
    p = models.StudentProfile(user_id=u.id, registration_number=f"R{tag}", current_class_id=cls.id); db.add(p); db.commit()
    par = None
    if parent:
        par = models.User(email=f"p_{tag}@x.com", hashed_password="x", full_name="Parent", role=models.UserRole.PARENT, school_id=school.id, is_active=True)
        db.add(par); db.flush()
        db.add(models.ParentStudentLink(parent_user_id=par.id, student_id=p.id, is_active=True)); db.commit()
    return u, p, par


def _assignment(db, teacher, school, cls, subject, **kw):
    payload = {
        "title": "Devoir 1", "assignment_type": "devoir", "mode": "online",
        "class_id": cls.id, "subject_id": subject.id, "max_score": 20,
        "answer_key": {"items": [{"id": 1, "expected_answer": "4", "points": 20}]},
        **kw,
    }
    a = svc.create_assignment(db, teacher, school.id, payload=payload)
    db.commit()
    return a


def test_create_publish_notifies_class():
    db = _session()
    school = _school(db); teacher = _teacher(db, school); cls, subject = _class_subject(db, school)
    su, sp, _ = _student(db, school, cls)
    a = _assignment(db, teacher, school, cls, subject, due_date=datetime.utcnow() + timedelta(days=3))
    assert a.status == models.AssignmentStatus.DRAFT

    svc.publish(db, a, teacher); db.commit()
    assert a.status == models.AssignmentStatus.PUBLISHED
    notif = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "assignment.published").one()
    assert notif.recipient_user_id == su.id and notif.source_id == a.id


def test_ai_generate_splits_content_and_answer_key(monkeypatch):
    db = _session()
    school = _school(db); teacher = _teacher(db, school)
    monkeypatch.setattr(ai_service, "generate_response_from_config", lambda p, c, d: {
        "data": '{"questions":[{"id":1,"type":"mcq","prompt":"2+2?","options":["3","4"],"points":10,"expected_answer":"4","explanation":"addition","skill":"calcul"},{"id":2,"type":"open","prompt":"Expliquez","points":10,"expected_answer":"…","explanation":"…","skill":"rédaction"}],"rubric":"barème","total_points":20}',
        "model_name": "mock",
    })
    out = svc.generate_ai(db, teacher, subject="Maths", level="6eme", num_questions=2)
    db.commit()
    # content has questions WITHOUT answers; answer_key has the corrigé.
    q0 = out["content"]["questions"][0]
    assert "expected_answer" not in q0 and q0["prompt"] == "2+2?"
    assert out["answer_key"]["items"][0]["expected_answer"] == "4"
    assert out["max_score"] == 20


def test_submit_flow_and_late_lock():
    db = _session()
    school = _school(db); teacher = _teacher(db, school); cls, subject = _class_subject(db, school)
    su, sp, _ = _student(db, school, cls)
    # Past due, no late penalty -> locked.
    a = _assignment(db, teacher, school, cls, subject, due_date=datetime.utcnow() - timedelta(days=1))
    svc.publish(db, a, teacher); db.commit()
    try:
        svc.submit(db, a, sp, answers={"1": "4"}); assert False
    except HTTPException as exc:
        assert exc.status_code == 409

    # Future due -> submit works, notifies teacher.
    a2 = _assignment(db, teacher, school, cls, subject, title="Devoir 2", due_date=datetime.utcnow() + timedelta(days=2))
    svc.publish(db, a2, teacher); db.commit()
    sub = svc.submit(db, a2, sp, answers={"1": "4"}); db.commit()
    assert sub.workflow_status == "submitted" and sub.is_late is False
    assert db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "assignment.submitted").count() == 1


def test_grade_notifies_student_and_parent_and_pushes_gradebook():
    db = _session()
    school = _school(db); teacher = _teacher(db, school); cls, subject = _class_subject(db, school)
    su, sp, parent = _student(db, school, cls, parent=True)
    # a current year + term so push-to-gradebook can build an assessment.
    year = models.AcademicYear(name="Y", school_id=school.id, is_current=True, start_date=datetime.utcnow() - timedelta(days=100), end_date=datetime.utcnow() + timedelta(days=100))
    db.add(year); db.flush()
    db.add(models.Term(name="T1", academic_year_id=year.id, start_date=year.start_date, end_date=year.end_date)); db.commit()

    a = _assignment(db, teacher, school, cls, subject, due_date=datetime.utcnow() + timedelta(days=2))
    svc.publish(db, a, teacher); sub = svc.submit(db, a, sp, answers={"1": "4"}); db.commit()

    svc.grade(db, sub, teacher, score=17, feedback="Bien"); db.commit()
    assert sub.workflow_status == "graded" and sub.score == 17
    graded_notifs = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "assignment.graded").all()
    assert {n.recipient_user_id for n in graded_notifs} == {su.id, parent.id}

    result = svc.push_to_gradebook(db, a, teacher); db.commit()
    assert result["created"] == 1
    grade_row = db.query(models.Grade).one()
    assert grade_row.score == 17


def test_ai_grade_is_proposal_until_confirmed(monkeypatch):
    db = _session()
    school = _school(db); teacher = _teacher(db, school); cls, subject = _class_subject(db, school)
    su, sp, _ = _student(db, school, cls)
    a = _assignment(db, teacher, school, cls, subject, due_date=datetime.utcnow() + timedelta(days=2))
    svc.publish(db, a, teacher); sub = svc.submit(db, a, sp, answers={"1": "4"}); db.commit()

    monkeypatch.setattr(ai_service, "generate_response_from_config", lambda p, c, d: {
        "data": '{"score":18,"feedback":"Presque parfait","errors":[],"strengths":["méthode"],"weaknesses":[],"advice":["revoir Q2"]}',
        "model_name": "mock",
    })
    proposal = svc.ai_grade(db, sub, teacher); db.commit()
    assert proposal["score"] == 18 and sub.ai_graded is True
    # Not final: still not "graded" until the teacher publishes.
    assert sub.workflow_status == "submitted"
    svc.grade(db, sub, teacher, score=18, feedback=proposal["feedback"]); db.commit()
    assert sub.workflow_status == "graded"


def test_answer_key_release_control():
    db = _session()
    school = _school(db); teacher = _teacher(db, school); cls, subject = _class_subject(db, school)
    now = datetime.utcnow()
    never = _assignment(db, teacher, school, cls, subject, title="N", answer_key_release="never", due_date=now - timedelta(days=1))
    immediate = _assignment(db, teacher, school, cls, subject, title="I", answer_key_release="immediate")
    after_before = _assignment(db, teacher, school, cls, subject, title="AB", answer_key_release="after_due", due_date=now + timedelta(days=1))
    after_after = _assignment(db, teacher, school, cls, subject, title="AA", answer_key_release="after_due", due_date=now - timedelta(days=1))
    assert svc.answer_key_visible_to_student(never) is False
    assert svc.answer_key_visible_to_student(immediate) is True
    assert svc.answer_key_visible_to_student(after_before) is False
    assert svc.answer_key_visible_to_student(after_after) is True


def test_endpoint_rbac_and_student_targeting():
    db = _session()
    school = _school(db); teacher = _teacher(db, school); cls, subject = _class_subject(db, school)
    su, sp, _ = _student(db, school, cls)
    su2, sp2, _ = _student(db, school, cls)
    # Targeted to sp only.
    a = _assignment(db, teacher, school, cls, subject, target_student_ids=[sp.id], due_date=datetime.utcnow() + timedelta(days=2))
    svc.publish(db, a, teacher); db.commit()

    # sp2 (not targeted) cannot submit.
    try:
        svc.submit(db, a, sp2, answers={"1": "4"}); assert False
    except HTTPException as exc:
        assert exc.status_code == 403

    # Student cannot create; teacher endpoint refuses students.
    try:
        R.create_assignment(payload=R.AssignmentCreate(title="X", class_id=cls.id), db=db, current_user=su)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 403

    # /mine returns only the targeted assignment for sp, empty for sp2.
    mine = R.my_assignments(student_id=None, db=db, current_user=su)
    assert len(mine) == 1 and mine[0]["id"] == a.id
    assert R.my_assignments(student_id=None, db=db, current_user=su2) == []
