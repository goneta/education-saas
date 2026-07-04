import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.services import ai_credits, grade_ocr
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
    teacher = models.User(email=f"t_{tag}@example.com", hashed_password="x", full_name=f"T {tag}", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add(teacher); db.commit()
    if credits:
        wallet = ai_credits.wallet_for_user(db, teacher)
        wallet.balance_credits = credits
        db.commit()
    return teacher


def _assessment_with_roster(db, school, names):
    tag = uuid.uuid4().hex[:4]
    cls = models.Class(name=f"C{tag}", school_id=school.id)
    db.add(cls); db.flush()
    subject = models.Subject(name=f"Maths {tag}", school_id=school.id)
    db.add(subject); db.flush()
    year = models.AcademicYear(name=f"Y{tag}", school_id=school.id, is_current=True,
                               start_date=datetime.utcnow() - timedelta(days=100), end_date=datetime.utcnow() + timedelta(days=200))
    db.add(year); db.flush()
    term = models.Term(name="T1", academic_year_id=year.id, start_date=year.start_date, end_date=year.end_date)
    db.add(term); db.flush()
    assessment = models.Assessment(title=f"Contrôle {tag}", date=datetime.utcnow() - timedelta(days=1), max_score=20,
                                   class_id=cls.id, subject_id=subject.id, term_id=term.id)
    db.add(assessment); db.flush()
    profiles = {}
    for name in names:
        stag = uuid.uuid4().hex[:5]
        user = models.User(email=f"stu_{stag}@example.com", hashed_password="x", full_name=name, role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
        db.add(user); db.flush()
        profile = models.StudentProfile(user_id=user.id, registration_number=f"R{stag}", current_class_id=cls.id)
        db.add(profile); db.flush()
        profiles[name] = profile
    db.commit()
    return assessment, profiles


def _mock_vision(monkeypatch, content):
    monkeypatch.setattr(ai_service, "generate_vision_response",
                        lambda prompt, image_base64, mime_type, db: {"content": content, "model_name": "mock-vision"})


def test_scan_maps_extracted_names_to_roster(monkeypatch):
    db = _session()
    school = _school(db)
    teacher = _teacher(db, school)
    assessment, profiles = _assessment_with_roster(db, school, ["Marie Dupont", "Jean Kouassi", "Awa Traoré"])
    _mock_vision(monkeypatch, '[{"name": "DUPONT Marie", "score": 14}, {"name": "Kouassi J.", "score": 9.5}, {"name": "Inconnu Test", "score": 12}]')

    result = grade_ocr.scan_grade_sheet(db, assessment.id, school.id, teacher, image_bytes=b"fake-image", mime_type="image/jpeg")
    db.commit()

    by_name = {p["student_name"]: p for p in result["proposals"]}
    assert by_name["Marie Dupont"]["score"] == 14 and by_name["Marie Dupont"]["confidence"] >= 0.9  # order-insensitive match
    assert by_name["Jean Kouassi"]["score"] == 9.5
    assert [u["name"] for u in result["unmatched"]] == ["Inconnu Test"]
    assert [m["student_name"] for m in result["missing_students"]] == ["Awa Traoré"]
    assert result["model_name"] == "mock-vision"


def test_scan_guards(monkeypatch):
    db = _session()
    school = _school(db)
    teacher = _teacher(db, school)
    assessment, _profiles = _assessment_with_roster(db, school, ["Marie Dupont"])

    # Unsupported mime type -> 415.
    try:
        grade_ocr.scan_grade_sheet(db, assessment.id, school.id, teacher, image_bytes=b"x", mime_type="application/pdf")
        assert False
    except HTTPException as exc:
        assert exc.status_code == 415

    # No vision provider configured -> honest 503 (never faked).
    def _raise(prompt, image_base64, mime_type, db):
        raise RuntimeError("No vision-capable AI provider is reachable.")
    monkeypatch.setattr(ai_service, "generate_vision_response", _raise)
    try:
        grade_ocr.scan_grade_sheet(db, assessment.id, school.id, teacher, image_bytes=b"x", mime_type="image/jpeg")
        assert False
    except HTTPException as exc:
        assert exc.status_code == 503

    # Another school's assessment -> 404.
    other_school = _school(db)
    _mock_vision(monkeypatch, "[]")
    try:
        grade_ocr.scan_grade_sheet(db, assessment.id, other_school.id, teacher, image_bytes=b"x", mime_type="image/jpeg")
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404


def test_confirm_upserts_and_validates():
    db = _session()
    school = _school(db)
    teacher = _teacher(db, school)
    assessment, profiles = _assessment_with_roster(db, school, ["Marie Dupont", "Jean Kouassi"])
    marie, jean = profiles["Marie Dupont"], profiles["Jean Kouassi"]
    db.add(models.Grade(assessment_id=assessment.id, student_id=marie.id, score=8))
    db.commit()

    entries = [
        schemas.GradeOcrConfirmEntry(student_id=marie.id, score=14),   # update
        schemas.GradeOcrConfirmEntry(student_id=jean.id, score=9.5),   # create
    ]
    summary = grade_ocr.confirm_grades(db, assessment.id, school.id, teacher, entries=entries)
    db.commit()
    assert summary == {"assessment_id": assessment.id, "created": 1, "updated": 1}

    scores = {g.student_id: g.score for g in db.query(models.Grade).filter(models.Grade.assessment_id == assessment.id).all()}
    assert scores[marie.id] == 14 and scores[jean.id] == 9.5

    # Out-of-range score -> 422; student outside the class -> 422.
    try:
        grade_ocr.confirm_grades(db, assessment.id, school.id, teacher, entries=[schemas.GradeOcrConfirmEntry(student_id=marie.id, score=25)])
        assert False
    except HTTPException as exc:
        assert exc.status_code == 422
    try:
        grade_ocr.confirm_grades(db, assessment.id, school.id, teacher, entries=[schemas.GradeOcrConfirmEntry(student_id=999999, score=10)])
        assert False
    except HTTPException as exc:
        assert exc.status_code == 422


def test_parse_entries_tolerates_fences_and_junk():
    content = "Voici le résultat :\n```json\n[{\"name\": \"A B\", \"score\": 12}, {\"name\": \"\", \"score\": 5}, {\"name\": \"C D\", \"score\": \"bad\"}]\n```"
    entries = grade_ocr._parse_entries(content)
    assert entries == [{"name": "A B", "score": 12.0}]
    assert grade_ocr._parse_entries("no json here") == []
