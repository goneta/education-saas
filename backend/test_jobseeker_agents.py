import uuid

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import employment as employment_router
from backend.services import ai_credits, jobseeker_agents


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _student_with_cv(db, skills=None, credits=1000):
    tag = uuid.uuid4().hex[:5]
    user = models.User(email=f"stu_{tag}@example.com", hashed_password="x", full_name=f"Student {tag}", role=models.UserRole.STUDENT, is_active=True)
    db.add(user); db.flush()
    cv = models.StudentCV(user_id=user.id, sharecode=f"SC{tag}", share_enabled=True, is_external=True,
                          looking_for_job=True, skills=skills or ["python"], languages=["francais"],
                          professional_title="Développeur junior", summary="Passionné de backend.",
                          external_identity={"first_name": "Stu", "last_name": tag})
    db.add(cv); db.commit()
    if credits:
        wallet = ai_credits.wallet_for_user(db, user)
        wallet.balance_credits = credits
        db.commit()
    return user, cv


def _published_offer(db, required=None, desired=None, languages=None, years=0, status="published"):
    tag = uuid.uuid4().hex[:5]
    rec_user = models.User(email=f"rec_{tag}@example.com", hashed_password="x", full_name="R", role=models.UserRole.RECRUITER, is_active=True)
    db.add(rec_user); db.flush()
    recruiter = models.RecruiterProfile(user_id=rec_user.id, company_name=f"Corp {tag}", sector="informatique", payment_status="confirmed", is_active=True)
    db.add(recruiter); db.flush()
    offer = models.JobOffer(recruiter_id=recruiter.id, title="Dev Python", company=recruiter.company_name,
                            sector="informatique", description="Backend Python.",
                            required_skills=required or ["python", "sql"], desired_skills=desired or ["docker"],
                            required_languages=languages or ["francais", "anglais"],
                            required_years_experience=years, status=status)
    db.add(offer); db.commit()
    return offer


def test_cv_refresh_updates_experience_and_timestamp():
    db = _session()
    user, cv = _student_with_cv(db)
    assert cv.last_auto_updated_at is None

    summary = employment_router.refresh_my_cv(current_user=user, db=db)
    assert summary["cv_id"] == cv.id and summary["refreshed_at"] is not None
    db.refresh(cv)
    assert cv.last_auto_updated_at is not None


def test_gap_analysis_lists_missing_items():
    db = _session()
    user, cv = _student_with_cv(db, skills=["python"])
    offer = _published_offer(db, required=["python", "sql"], desired=["docker"], languages=["francais", "anglais"], years=2)

    result = jobseeker_agents.gap_analysis(db, offer.id, cv, user)
    assert result["missing_required_skills"] == ["sql"]
    assert result["missing_desired_skills"] == ["docker"]
    assert result["missing_languages"] == ["anglais"]
    assert result["experience_gap_years"] == 2
    assert result["advice"]


def test_cover_letter_grounded_and_unpublished_offer_hidden():
    db = _session()
    user, cv = _student_with_cv(db)
    offer = _published_offer(db)

    result = jobseeker_agents.draft_cover_letter(db, offer.id, cv, user)
    assert result["job_id"] == offer.id and result["letter"]

    draft = _published_offer(db, status="draft")
    for fn in (jobseeker_agents.gap_analysis, jobseeker_agents.draft_cover_letter):
        try:
            fn(db, draft.id, cv, user)
            assert False
        except HTTPException as exc:
            assert exc.status_code == 404


def test_endpoints_require_cv():
    db = _session()
    tag = uuid.uuid4().hex[:5]
    teacher = models.User(email=f"t_{tag}@example.com", hashed_password="x", full_name="T", role=models.UserRole.TEACHER, is_active=True)
    db.add(teacher); db.commit()

    try:
        employment_router.refresh_my_cv(current_user=teacher, db=db)
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404  # no CV / student profile
