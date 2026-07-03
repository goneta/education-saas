"""Recruiter automations (automation D, recruiters group).

- **Saved-search agents**: a recruiter stores candidate criteria (sector,
  skills, languages, minimum score); the runner re-scores only CVs updated
  since the search's `last_run_at` watermark and notifies the recruiter
  (`EmploymentNotification`) about NEW matching graduates — scheduled runs
  never re-flag old matches.
- **Screening questionnaires**: one AI generation per offer (credit-gated)
  producing 5–8 screening questions grounded in the offer's description and
  required skills; stored on `JobOffer.screening_questions` for reuse.
- **Match reasons**: an on-demand AI explanation of why a specific candidate
  ranks where they do against an offer, grounded in the deterministic
  `match_score` details (credit-gated).
"""

from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models
from ..services.ai_service import ai_service
from . import ai_credits, employment


def _criteria_offer(criteria: dict) -> SimpleNamespace:
    """Adapter: saved-search criteria scored through the same match engine as offers."""
    criteria = criteria or {}
    return SimpleNamespace(
        sector=criteria.get("sector"),
        required_skills=criteria.get("skills") or [],
        desired_skills=[],
        required_languages=criteria.get("languages") or [],
        required_years_experience=criteria.get("min_experience_years") or 0,
    )


def run_saved_search(db: Session, search: models.RecruiterSavedSearch, current_user: models.User) -> dict:
    """Score CVs updated since the watermark; notify the recruiter on new matches."""
    criteria = search.criteria or {}
    min_score = int(criteria.get("min_score") or 50)
    pseudo_offer = _criteria_offer(criteria)

    query = db.query(models.StudentCV).filter(
        models.StudentCV.share_enabled == True,  # noqa: E712
        models.StudentCV.looking_for_job == True,  # noqa: E712
    )
    if search.last_run_at:
        query = query.filter(or_(
            models.StudentCV.updated_at >= search.last_run_at,
            models.StudentCV.created_at >= search.last_run_at,
        ))
    candidates = query.limit(500).all()

    matches = []
    for cv in candidates:
        details = employment.match_score(pseudo_offer, cv)
        if details["score"] >= min_score:
            matches.append({"cv": employment.public_cv_payload(cv), "score": details["score"], "details": details})
    matches.sort(key=lambda item: item["score"], reverse=True)

    if matches:
        db.add(models.EmploymentNotification(
            audience="recruiter",
            recruiter_id=search.recruiter_id,
            title=f"Agent « {search.name} » : {len(matches)} nouveau(x) profil(s)",
            message=f"{len(matches)} candidat(s) correspondent à votre recherche enregistrée « {search.name} » (score ≥ {min_score}).",
            payload={"saved_search_id": search.id, "matches": [{"cv_id": m["cv"]["id"], "score": m["score"]} for m in matches[:10]]},
            created_by_id=current_user.id,
        ))
    # 1-second overlap: DB server timestamps have second resolution and the
    # bound parameter carries microseconds, so an exact watermark would skip
    # rows created in the same second as the run. A CV re-scored inside the
    # overlap only re-enters the aggregate notification — never a duplicate row.
    search.last_run_at = datetime.utcnow().replace(microsecond=0) - timedelta(seconds=1)

    return {"search_id": search.id, "name": search.name, "scanned": len(candidates), "matches": matches[:10], "match_count": len(matches), "notified": bool(matches)}


def generate_screening_questions(
    db: Session,
    job: models.JobOffer,
    current_user: models.User,
    *,
    num_questions: int = 6,
    language: str = "fr",
) -> dict:
    """AI screening questionnaire grounded in the offer; stored on the offer."""
    skills = ", ".join((job.required_skills or []) + (job.desired_skills or [])) or "—"
    prompt = (
        f"Create {num_questions} screening questions in {language} for the job offer "
        f"'{job.title}' at '{job.company}' (sector: {job.sector}"
        f"{f', contract: {job.contract_type}' if job.contract_type else ''}). "
        f"Key skills: {skills}. Offer description: {(job.description or '')[:1500]}. "
        "Mix knowledge checks, one practical scenario and one motivation question. For each "
        "question add in one line what a strong answer should contain. Number the questions."
    )
    ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(prompt))
    result = ai_service.generate_response_from_config(prompt, {"module": "automation_screening"}, db)
    content = result.get("data") or result.get("message") or ""
    ai_credits.record_usage(db, current_user, prompt, content, "automation_screening", "screening_questions")

    job.screening_questions = {"questions": content, "num_questions": num_questions, "language": language, "generated_at": datetime.utcnow().isoformat()}
    return {"job_id": job.id, "questions": content}


def explain_match(
    db: Session,
    job: models.JobOffer,
    cv_id: int,
    current_user: models.User,
    *,
    language: str = "fr",
) -> dict:
    """AI-written reasons for one candidate's ranking against an offer."""
    cv = db.query(models.StudentCV).filter(models.StudentCV.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV introuvable.")
    details = employment.match_score(job, cv)
    payload = employment.public_cv_payload(cv)

    prompt = (
        f"In {language}, explain to a recruiter in a short paragraph plus 3 bullet points why "
        f"candidate '{payload.get('name') or cv.id}' scores "
        f"{details['score']}/100 for the offer '{job.title}' ({job.sector}). "
        f"Matched required skills: {', '.join(details['required_skill_matches']) or 'none'}. "
        f"Matched desired skills: {', '.join(details['desired_skill_matches']) or 'none'}. "
        f"Languages matched: {', '.join(details['language_matches']) or 'none'}. "
        f"Sector match: {details['sector_match']}. Experience: {details['experience_years']} year(s) "
        f"vs {job.required_years_experience or 0} required. "
        "Also name the main gap to probe in an interview. Stay factual — only use the data given."
    )
    ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(prompt))
    result = ai_service.generate_response_from_config(prompt, {"module": "automation_match_reasons"}, db)
    content = result.get("data") or result.get("message") or ""
    ai_credits.record_usage(db, current_user, prompt, content, "automation_match_reasons", "explain_match")

    return {"job_id": job.id, "cv_id": cv.id, "score": details["score"], "details": details, "reasons": content}
