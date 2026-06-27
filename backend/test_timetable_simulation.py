from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.services import timetable_optimizer, timetable_simulation


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _fixtures(db, *, classes=2, subjects=4, teachers=2):
    school = models.School(name="Sim", domain_prefix="sim", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    for c in range(classes):
        db.add(models.Class(name=f"C{c}", level="6", school_id=school.id))
    for s in range(subjects):
        db.add(models.Subject(name=f"S{s}", code=f"S{s}", school_id=school.id))
    for t in range(teachers):
        db.add(models.User(email=f"t{t}@sim.local", hashed_password="x", full_name=f"T{t}", role=models.UserRole.TEACHER, school=school, is_active=True))
    db.commit()
    return school


def test_explain_candidate_produces_statements():
    db = _session()
    school = _fixtures(db)
    best = timetable_optimizer.generate_candidates(db, school.id, candidate_count=1)[0]
    statements = timetable_simulation.explain_candidate(best)
    assert any("Score de qualité" in s for s in statements)
    assert any("placées" in s for s in statements)


def test_simulate_teacher_absent_reports_impact():
    db = _session()
    school = _fixtures(db, classes=2, subjects=6, teachers=2)
    teacher = db.query(models.User).filter(models.User.role == models.UserRole.TEACHER).first()
    result = timetable_simulation.simulate(db, school.id, "teacher_absent", {"teacher_id": teacher.id})
    assert result["scenario"] == "teacher_absent"
    assert "baseline" in result and "scenario_result" in result
    assert isinstance(result["impact"], list) and result["impact"]
    # Fewer teachers cannot improve coverage.
    assert result["scenario_result"]["unplaced"] >= result["baseline"]["unplaced"]


def test_simulate_extra_working_day_does_not_worsen():
    db = _session()
    school = _fixtures(db)
    result = timetable_simulation.simulate(db, school.id, "extra_working_day", {"day": "saturday"})
    assert result["scenario"] == "extra_working_day"
    # Adding capacity should not increase unplaced sessions.
    assert result["scenario_result"]["unplaced"] <= result["baseline"]["unplaced"]


def test_simulate_unknown_scenario():
    db = _session()
    school = _fixtures(db)
    assert timetable_simulation.simulate(db, school.id, "nonsense", {}).get("error")
