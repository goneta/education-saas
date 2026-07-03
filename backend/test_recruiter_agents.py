import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import employment as employment_router
from backend.services import ai_credits, recruiter_agents


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _recruiter(db, credits=1000, payment_status="confirmed"):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"rec_{tag}@example.com", hashed_password="x", full_name=f"Rec {tag}", role=models.UserRole.RECRUITER, is_active=True)
    db.add(user); db.flush()
    recruiter = models.RecruiterProfile(user_id=user.id, company_name=f"Corp {tag}", sector="informatique", payment_status=payment_status, is_active=True)
    db.add(recruiter); db.commit()
    if credits:
        wallet = ai_credits.wallet_for_user(db, user)
        wallet.balance_credits = credits
        db.commit()
    return user, recruiter


def _cv(db, skills, sectors=None, languages=None, looking=True, age_hours=0):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"cv_{tag}@example.com", hashed_password="x", full_name=f"Cand {tag}", role=models.UserRole.STUDENT, is_active=True)
    db.add(user); db.flush()
    cv = models.StudentCV(user_id=user.id, sharecode=f"SC{tag}", share_enabled=True, is_external=True,
                          looking_for_job=looking, skills=skills, sectors=sectors or ["informatique"],
                          languages=languages or ["francais"],
                          external_identity={"first_name": "Cand", "last_name": tag})
    if age_hours:
        stamp = datetime.utcnow() - timedelta(hours=age_hours)
        cv.created_at = stamp
        cv.updated_at = stamp
    db.add(cv); db.commit()
    return cv


def _offer(db, recruiter, skills=None):
    offer = models.JobOffer(recruiter_id=recruiter.id, title="Dev Python", company=recruiter.company_name,
                            sector="informatique", description="Développement backend Python/FastAPI.",
                            required_skills=skills or ["python", "sql"], desired_skills=["docker"],
                            required_languages=["francais"], status="published")
    db.add(offer); db.commit()
    return offer


def test_saved_search_matches_and_watermark():
    db = _session()
    user, recruiter = _recruiter(db)
    _cv(db, skills=["python", "sql"], age_hours=2)
    _cv(db, skills=["cuisine"], sectors=["restauration"], age_hours=2)  # low score, below min_score

    search = models.RecruiterSavedSearch(recruiter_id=recruiter.id, name="Devs Python",
                                         criteria={"sector": "informatique", "skills": ["python", "sql"], "min_score": 70})
    db.add(search); db.commit()

    first = recruiter_agents.run_saved_search(db, search, user)
    db.commit()
    assert first["match_count"] == 1 and first["notified"] is True
    assert search.last_run_at is not None
    notif = db.query(models.EmploymentNotification).filter(models.EmploymentNotification.audience == "recruiter").one()
    assert notif.recruiter_id == recruiter.id and "Devs Python" in notif.title

    # Second run: no CV changed since the watermark -> nothing new, no notification.
    second = recruiter_agents.run_saved_search(db, search, user)
    db.commit()
    assert second["match_count"] == 0 and second["notified"] is False
    assert db.query(models.EmploymentNotification).count() == 1

    # A NEW matching CV is picked up on the next run.
    _cv(db, skills=["python", "sql", "docker"])
    third = recruiter_agents.run_saved_search(db, search, user)
    db.commit()
    assert third["match_count"] == 1
    assert db.query(models.EmploymentNotification).count() == 2


def test_screening_questions_stored_on_offer():
    db = _session()
    user, recruiter = _recruiter(db)
    offer = _offer(db, recruiter)

    result = recruiter_agents.generate_screening_questions(db, offer, user, num_questions=5)
    db.commit()
    assert result["questions"]
    db.refresh(offer)
    assert offer.screening_questions and offer.screening_questions["num_questions"] == 5


def test_explain_match_grounded_in_details():
    db = _session()
    user, recruiter = _recruiter(db)
    offer = _offer(db, recruiter)
    cv = _cv(db, skills=["python"])

    result = recruiter_agents.explain_match(db, offer, cv.id, user)
    assert result["cv_id"] == cv.id and result["reasons"]
    assert "python" in result["details"]["required_skill_matches"]

    try:
        recruiter_agents.explain_match(db, offer, 999999, user)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404


def test_endpoint_scoping_and_payment_gate():
    db = _session()
    user_a, recruiter_a = _recruiter(db)
    user_b, recruiter_b = _recruiter(db)
    offer_b = _offer(db, recruiter_b)

    # Recruiter A cannot touch recruiter B's offer.
    try:
        employment_router.generate_screening_questions(job_id=offer_b.id, num_questions=6, language="fr", current_user=user_a, db=db)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404

    # Saved searches are per-recruiter.
    row = employment_router.create_saved_search(payload=schemas.RecruiterSavedSearchCreate(name="Ma recherche", criteria={"skills": ["python"]}), current_user=user_a, db=db)
    assert row.id
    assert employment_router.list_saved_searches(current_user=user_b, db=db) == []
    try:
        employment_router.run_saved_search(search_id=row.id, current_user=user_b, db=db)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404

    # Unpaid recruiter is blocked (402).
    user_c, _rec_c = _recruiter(db, payment_status="pending")
    try:
        employment_router.create_saved_search(payload=schemas.RecruiterSavedSearchCreate(name="Blocked search", criteria={}), current_user=user_c, db=db)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 402
