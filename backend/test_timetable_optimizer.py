from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import timetable_optimizer


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _fixtures(db, *, classes=2, subjects=3, teachers=2):
    school = models.School(name="Opt", domain_prefix="opt", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    for c in range(classes):
        db.add(models.Class(name=f"C{c}", level="6", school_id=school.id))
    for s in range(subjects):
        db.add(models.Subject(name=f"S{s}", code=f"S{s}", school_id=school.id, coefficient=1))
    for t in range(teachers):
        db.add(models.User(email=f"t{t}@opt.local", hashed_password="x", full_name=f"T{t}", role=models.UserRole.TEACHER, school=school, is_active=True))
    db.commit()
    return school


def test_generate_candidates_are_scored_and_sorted():
    db = _session()
    school = _fixtures(db)
    candidates = timetable_optimizer.generate_candidates(db, school.id, candidate_count=3)
    assert len(candidates) == 3
    scores = [c.score for c in candidates]
    assert scores == sorted(scores, reverse=True)
    for c in candidates:
        assert 0 <= c.score <= 100
        assert "fill_rate" in c.breakdown


def test_candidates_have_no_hard_conflicts():
    db = _session()
    school = _fixtures(db)
    best = timetable_optimizer.generate_candidates(db, school.id, candidate_count=2)[0]
    class_slots = set()
    teacher_slots = set()
    for p in best.placements:
        ckey = (p.class_id, p.day, p.start)
        assert ckey not in class_slots, "class double-booked"
        class_slots.add(ckey)
        if p.teacher_id:
            tkey = (p.teacher_id, p.day, p.start)
            assert tkey not in teacher_slots, "teacher double-booked"
            teacher_slots.add(tkey)


def test_optimizer_respects_teacher_availability_rule():
    db = _session()
    school = _fixtures(db, classes=1, subjects=2, teachers=1)
    teacher = db.query(models.User).filter(models.User.role == models.UserRole.TEACHER).first()
    db.add(models.TimetableConstraintRule(
        school_id=school.id, rule_type="teacher_available_days",
        parameters={"teacher_id": teacher.id, "days": ["tuesday"]}, is_active=True,
    ))
    db.commit()
    best = timetable_optimizer.generate_candidates(db, school.id, candidate_count=2)[0]
    for p in best.placements:
        if p.teacher_id == teacher.id:
            assert p.day == "tuesday"
