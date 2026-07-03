"""Job-seeker automations (automation D, job-seeking students/graduates).

- **CV auto-refresh**: rebuilds the caller's CV from their real academic
  record (existing `build_academic_snapshot`) and recomputes experience —
  the same mechanic the year-closure flow uses, exposed on demand to the
  student so grades and credentials flow into the CV page without manual
  editing.
- **Gap analysis**: deterministic diff between an offer's requirements and
  the CV (missing required/desired skills, languages, experience gap from
  the existing `match_score`), followed by AI advice on how to close each
  gap (credit-gated).
- **Cover letters**: an AI draft grounded STRICTLY in the CV's real data
  (title, summary, skills, academic timeline, experience) and the offer —
  the prompt forbids inventing facts (credit-gated).
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..services.ai_service import ai_service
from . import ai_credits, employment


def refresh_my_cv(db: Session, cv: models.StudentCV, current_user: models.User) -> dict:
    """Pull the student's real academic record into the CV (on-demand)."""
    timeline_entries = 0
    if cv.student_global_profile_id:
        profile = db.query(models.StudentGlobalProfile).filter(models.StudentGlobalProfile.id == cv.student_global_profile_id).first()
        if profile:
            cv.academic_timeline = employment.build_academic_snapshot(db, profile)
            timeline_entries = len(cv.academic_timeline or [])
    cv.total_experience_years = employment.calculate_experience_years(cv)
    cv.last_auto_updated_at = employment._utcnow()
    return {
        "cv_id": cv.id,
        "timeline_entries": timeline_entries,
        "experience_years": cv.total_experience_years,
        "refreshed_at": cv.last_auto_updated_at,
    }


def _published_job(db: Session, job_id: int) -> models.JobOffer:
    job = db.query(models.JobOffer).filter(models.JobOffer.id == job_id, models.JobOffer.status == "published").first()
    if not job:
        raise HTTPException(status_code=404, detail="Offre introuvable ou non publiée.")
    return job


def gap_analysis(db: Session, job_id: int, cv: models.StudentCV, current_user: models.User, *, language: str = "fr") -> dict:
    """Offer→profile gaps (deterministic) + AI advice on closing them."""
    job = _published_job(db, job_id)
    details = employment.match_score(job, cv)
    cv_skills = {skill.lower() for skill in ((cv.skills or []) + (cv.detailed_skills or []))}
    missing_required = sorted({s for s in (job.required_skills or []) if s.lower() not in cv_skills})
    missing_desired = sorted({s for s in (job.desired_skills or []) if s.lower() not in cv_skills})
    cv_languages = {lang.lower() for lang in (cv.languages or [])}
    missing_languages = sorted({l for l in (job.required_languages or []) if l.lower() not in cv_languages})
    experience_gap = max((job.required_years_experience or 0) - (details["experience_years"] or 0), 0)

    prompt = (
        f"In {language}, advise a job-seeking student on closing the gaps between their profile and "
        f"the offer '{job.title}' ({job.sector}). Their match score is {details['score']}/100. "
        f"Missing required skills: {', '.join(missing_required) or 'none'}. "
        f"Missing desired skills: {', '.join(missing_desired) or 'none'}. "
        f"Missing languages: {', '.join(missing_languages) or 'none'}. "
        f"Experience gap: {experience_gap} year(s). "
        "For EACH missing item, suggest one concrete way to acquire it (course type, certification, "
        "project or internship idea). If nothing is missing, say the profile is ready and suggest how "
        "to stand out. Keep it short, encouraging and actionable."
    )
    ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(prompt))
    result = ai_service.generate_response_from_config(prompt, {"module": "automation_gap_analysis"}, db)
    advice = result.get("data") or result.get("message") or ""
    ai_credits.record_usage(db, current_user, prompt, advice, "automation_gap_analysis", "gap_analysis")

    return {
        "job_id": job.id,
        "job_title": job.title,
        "score": details["score"],
        "missing_required_skills": missing_required,
        "missing_desired_skills": missing_desired,
        "missing_languages": missing_languages,
        "experience_gap_years": experience_gap,
        "advice": advice,
    }


def draft_cover_letter(db: Session, job_id: int, cv: models.StudentCV, current_user: models.User, *, language: str = "fr") -> dict:
    """AI cover-letter draft grounded strictly in the CV's real record."""
    job = _published_job(db, job_id)
    payload = employment.public_cv_payload(cv)
    timeline = "; ".join(
        str(entry.get("label") or entry.get("year") or entry) for entry in (cv.academic_timeline or [])[:6]
    )
    prompt = (
        f"Draft a short cover letter in {language} (under 250 words) for the offer '{job.title}' at "
        f"'{job.company}' ({job.sector}). Candidate facts — name: {payload.get('name') or 'the candidate'}; "
        f"title: {cv.professional_title or '—'}; summary: {(cv.summary or '—')[:400]}; "
        f"skills: {', '.join((cv.skills or [])[:12]) or '—'}; languages: {', '.join(cv.languages or []) or '—'}; "
        f"experience: {cv.total_experience_years or 0} year(s); academic record: {timeline or '—'}. "
        "Use ONLY these facts — do not invent diplomas, employers or achievements. Structure: hook, "
        "2 short paragraphs mapping the candidate's real strengths to the offer, closing with "
        "availability. First person, professional but warm."
    )
    ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(prompt))
    result = ai_service.generate_response_from_config(prompt, {"module": "automation_cover_letter"}, db)
    letter = result.get("data") or result.get("message") or ""
    ai_credits.record_usage(db, current_user, prompt, letter, "automation_cover_letter", "cover_letter")

    return {"job_id": job.id, "job_title": job.title, "letter": letter}
