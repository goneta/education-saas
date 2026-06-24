from __future__ import annotations

import re
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from .. import audit, database, models, schemas, security
from ..services import employment

router = APIRouter(prefix="/employment", tags=["TeducAI Emploi"])
logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _student_cv_for_user(db: Session, user: models.User) -> models.StudentCV:
    cv = db.query(models.StudentCV).options(selectinload(models.StudentCV.work_history)).filter(models.StudentCV.user_id == user.id).first()
    if cv:
        return cv
    profile = db.query(models.StudentGlobalProfile).filter(models.StudentGlobalProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Page CV introuvable.")
    return employment.ensure_student_cv(db, profile, current_user=user)


def _recruiter_for_user(db: Session, user: models.User) -> models.RecruiterProfile:
    row = db.query(models.RecruiterProfile).filter(models.RecruiterProfile.user_id == user.id, models.RecruiterProfile.is_active == True).first()  # noqa: E712
    if not row:
        raise HTTPException(status_code=403, detail="Compte recruteur TeducAI Emploi requis.")
    return row


def _require_recruiter_payment(recruiter: models.RecruiterProfile) -> None:
    if recruiter.payment_status != "confirmed":
        raise HTTPException(status_code=402, detail="Paiement: pending, must pay before using the service.")


def _safe_recruiter_payload(payload: schemas.RecruiterRegister) -> dict:
    data = payload.model_dump()
    data["password"] = "***"
    return data


def _database_accepts_recruiter_role(db: Session) -> bool:
    bind = db.get_bind()
    if bind.dialect.name != "postgresql":
        return True
    try:
        return bool(db.execute(text(
            "select 1 from pg_enum e join pg_type t on t.oid = e.enumtypid "
            "where t.typname = 'userrole' and e.enumlabel = 'recruiter'"
        )).first())
    except SQLAlchemyError:
        logger.exception("Recruiter role enum capability check failed; falling back to staff role")
        db.rollback()
        return False


def _require_paid_recruiter_if_authenticated(request: Request, db: Session) -> None:
    auth_header = request.headers.get("authorization") or ""
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
    except Exception:
        return
    email = payload.get("sub")
    if not email:
        return
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return
    recruiter = db.query(models.RecruiterProfile).filter(
        models.RecruiterProfile.user_id == user.id,
        models.RecruiterProfile.is_active == True,  # noqa: E712
    ).first()
    if recruiter:
        _require_recruiter_payment(recruiter)


def _cv_response(cv: models.StudentCV) -> dict:
    return {
        "id": cv.id,
        "sharecode": cv.sharecode,
        "share_enabled": cv.share_enabled,
        "is_external": cv.is_external,
        "professional_title": cv.professional_title,
        "summary": cv.summary,
        "sectors": cv.sectors or [],
        "looking_for_job": cv.looking_for_job,
        "cv_photo_url": cv.cv_photo_url,
        "privacy_settings": {**employment.DEFAULT_PRIVACY, **(cv.privacy_settings or {})},
        "academic_timeline": cv.academic_timeline or [],
        "skills": cv.skills or [],
        "languages": cv.languages or [],
        "portfolio": cv.portfolio or [],
        "availability": cv.availability,
        "external_identity": cv.external_identity,
        "work_history": cv.work_history,
        "created_at": cv.created_at,
        "updated_at": cv.updated_at,
    }


@router.get("/sectors")
def sectors():
    return {"sectors": employment.SECTORS}


@router.get("/jobs", response_model=list[schemas.JobOfferResponse])
def public_jobs(sector: str | None = None, db: Session = Depends(database.get_db)):
    query = db.query(models.JobOffer).filter(models.JobOffer.status == "published")
    if sector:
        query = query.filter(models.JobOffer.sector.ilike(f"%{sector}%"))
    return query.order_by(models.JobOffer.created_at.desc()).limit(100).all()


@router.get("/public-profiles")
def public_profiles(request: Request, sector: str | None = None, q: str | None = None, db: Session = Depends(database.get_db)):
    _require_paid_recruiter_if_authenticated(request, db)
    query = db.query(models.StudentCV).options(selectinload(models.StudentCV.work_history)).filter(
        models.StudentCV.looking_for_job == True,  # noqa: E712
        models.StudentCV.share_enabled == True,  # noqa: E712
    )
    rows = []
    for cv in query.order_by(models.StudentCV.updated_at.desc().nullslast(), models.StudentCV.id.desc()).limit(200).all():
        privacy = {**employment.DEFAULT_PRIVACY, **(cv.privacy_settings or {})}
        if not privacy.get("visible_in_sector_search"):
            continue
        haystack = " ".join((cv.sectors or []) + (cv.skills or []) + [cv.professional_title or "", cv.summary or ""]).lower()
        if sector and sector.lower() not in haystack:
            continue
        if q and q.lower() not in haystack:
            continue
        rows.append(employment.public_cv_payload(cv))
    return rows[:60]


@router.post("/sharecode/lookup")
def lookup_sharecode(payload: schemas.SharecodeLookup, request: Request, db: Session = Depends(database.get_db)):
    _require_paid_recruiter_if_authenticated(request, db)
    ip_address = request.client.host if request.client else None
    employment.rate_limit_sharecode(db, ip_address=ip_address)
    cv = db.query(models.StudentCV).options(selectinload(models.StudentCV.work_history)).filter(
        models.StudentCV.sharecode == payload.sharecode.strip().upper(),
        models.StudentCV.share_enabled == True,  # noqa: E712
    ).first()
    if not cv or (cv.share_expires_at and cv.share_expires_at < _now()):
        raise HTTPException(status_code=404, detail="Sharecode invalide ou expire.")
    db.add(models.StudentCVAccessLog(
        student_cv_id=cv.id,
        access_type="sharecode_lookup",
        sharecode_used=payload.sharecode.strip().upper(),
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent"),
    ))
    db.commit()
    return employment.public_cv_payload(cv)


@router.post("/external-students/register")
def register_external_student(payload: schemas.ExternalStudentRegister, db: Session = Depends(database.get_db)):
    if db.query(models.User.id).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Un compte existe deja avec cet email.")
    security.validate_password_strength(payload.password)
    user = models.User(
        email=payload.email,
        hashed_password=security.get_password_hash(payload.password),
        full_name=f"{payload.first_name} {payload.last_name}".strip(),
        role=models.UserRole.STUDENT,
        school_id=None,
        is_active=True,
    )
    db.add(user)
    db.flush()
    cv = models.StudentCV(
        user_id=user.id,
        is_external=True,
        sharecode=employment.generate_sharecode(db, first_name=payload.first_name, last_name=payload.last_name, external=True),
        professional_title=payload.professional_title,
        sectors=[payload.sector] if payload.sector else [],
        looking_for_job=True,
        privacy_settings={**employment.DEFAULT_PRIVACY, "visible_in_sector_search": True},
        external_identity={"first_name": payload.first_name, "last_name": payload.last_name, "phone": payload.phone},
        skills=[],
        languages=[],
        portfolio=[],
        academic_timeline=[],
    )
    db.add(cv)
    payment = models.PlatformPayment(
        reference=f"EMP-STU-{user.id}-{int(_now().timestamp())}",
        payer_user_id=user.id,
        payment_type="employment_external_student_registration",
        amount=0,
        currency="FCFA",
        provider=payload.payment_provider,
        status="confirmed" if payload.payment_provider == "free" else "pending",
        beneficiary_entity="platform",
        metadata_json={"module": "teducai_emploi"},
    )
    db.add(payment)
    audit.record_audit(db, action="employment.external_student.created", current_user=user, entity_type="student_cv", entity_id=cv.id)
    db.commit()
    return {"user_id": user.id, "student_cv_id": cv.id, "sharecode": cv.sharecode, "payment_status": payment.status}


@router.post("/recruiters/register")
def register_recruiter(payload: schemas.RecruiterRegister, request: Request, db: Session = Depends(database.get_db)):
    logger.info(
        "Recruiter registration received",
        extra={"payload": _safe_recruiter_payload(payload), "client": request.client.host if request.client else None},
    )
    try:
        if db.query(models.User.id).filter(models.User.email == payload.email).first():
            logger.info("Recruiter registration rejected: duplicate email", extra={"email": payload.email})
            raise HTTPException(status_code=409, detail=[{"loc": ["body", "email"], "msg": "Un compte existe deja avec cet email."}])
        if payload.phone and len(re.sub(r"\D", "", payload.phone)) < 6:
            logger.info("Recruiter registration rejected: invalid phone", extra={"email": payload.email})
            raise HTTPException(status_code=422, detail=[{"loc": ["body", "phone"], "msg": "Numero de telephone invalide."}])
        security.validate_password_strength(payload.password)
        logger.info("Recruiter registration validation passed", extra={"email": payload.email, "plan": payload.plan})

        recruiter_role = models.UserRole.RECRUITER if _database_accepts_recruiter_role(db) else models.UserRole.STAFF
        if recruiter_role == models.UserRole.STAFF:
            logger.warning("Recruiter enum value unavailable; using staff role with recruiter profile", extra={"email": payload.email})
        user = models.User(
            email=payload.email,
            hashed_password=security.get_password_hash(payload.password),
            full_name=payload.contact_name,
            role=recruiter_role,
            school_id=None,
            is_active=True,
        )
        db.add(user)
        db.flush()
        logger.info("Recruiter user row created", extra={"user_id": user.id, "role": user.role.value})

        plan_limits = {
            "promo": (1, 10),
            "sharecode_only": (0, 25),
            "job_posts": (5, 50),
            "cvtheque_limited": (3, 100),
            "cvtheque_advanced": (20, 1000),
        }
        offers_allowed, cv_views_allowed = plan_limits.get(payload.plan, (0, 25))
        recruiter = models.RecruiterProfile(
            user_id=user.id,
            company_name=payload.company_name,
            contact_name=payload.contact_name,
            sector=payload.sector,
            phone=payload.phone,
            website=payload.website,
            subscription_plan=payload.plan,
            payment_status="confirmed" if payload.payment_provider == "free" else "pending",
            offers_allowed=offers_allowed,
            cv_views_allowed=cv_views_allowed,
        )
        db.add(recruiter)
        db.flush()
        logger.info("Recruiter profile row created", extra={"user_id": user.id, "recruiter_id": recruiter.id, "payment_status": recruiter.payment_status})

        db.commit()
        db.refresh(user)
        db.refresh(recruiter)
        logger.info("Recruiter core registration committed", extra={"user_id": user.id, "recruiter_id": recruiter.id})
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        logger.exception("Recruiter registration database integrity failure", extra={"payload": _safe_recruiter_payload(payload)})
        raise HTTPException(status_code=409, detail="Un compte existe deja avec ces informations.")
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Recruiter registration database failure", extra={"payload": _safe_recruiter_payload(payload)})
        raise HTTPException(status_code=500, detail="Inscription recruteur indisponible pour le moment. Veuillez reessayer.")
    except Exception:
        db.rollback()
        logger.exception("Recruiter registration unexpected failure", extra={"payload": _safe_recruiter_payload(payload)})
        raise HTTPException(status_code=500, detail="Inscription recruteur indisponible pour le moment. Veuillez reessayer.")

    try:
        payment = models.PlatformPayment(
            reference=f"EMP-REC-{user.id}-{int(_now().timestamp())}",
            payer_user_id=user.id,
            payment_type="employment_recruiter_subscription",
            amount=0,
            currency="FCFA",
            provider=payload.payment_provider,
            status=recruiter.payment_status,
            beneficiary_entity="platform",
            metadata_json={"module": "teducai_emploi", "plan": payload.plan},
        )
        db.add(payment)
        db.flush()
        logger.info("Recruiter payment row created", extra={"user_id": user.id, "recruiter_id": recruiter.id, "payment_id": payment.id, "status": payment.status})
        audit.record_audit(db, action="employment.recruiter.created", current_user=user, entity_type="recruiter_profile", entity_id=recruiter.id)
        db.commit()
        logger.info("Recruiter payment and audit committed", extra={"user_id": user.id, "recruiter_id": recruiter.id})
    except Exception:
        db.rollback()
        logger.exception("Recruiter registration side effects failed after core account creation", extra={"user_id": user.id, "recruiter_id": recruiter.id})

    return {"user_id": user.id, "recruiter_id": recruiter.id, "payment_status": recruiter.payment_status}


@router.get("/recruiter/me")
def recruiter_me(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    return {
        "id": recruiter.id,
        "company_name": recruiter.company_name,
        "contact_name": recruiter.contact_name,
        "subscription_plan": recruiter.subscription_plan,
        "payment_status": recruiter.payment_status,
        "offers_allowed": recruiter.offers_allowed,
        "cv_views_allowed": recruiter.cv_views_allowed,
    }


@router.get("/me/cv")
def my_cv(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    db.commit()
    return _cv_response(cv)


@router.put("/me/cv")
def update_my_cv(payload: schemas.StudentCVUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "privacy_settings" and value is not None:
            value = {**employment.DEFAULT_PRIVACY, **value}
        setattr(cv, key, value)
    audit.record_audit(db, action="employment.cv.updated", current_user=current_user, entity_type="student_cv", entity_id=cv.id, details={"fields": sorted(updates.keys())})
    db.commit()
    db.refresh(cv)
    return _cv_response(cv)


@router.post("/me/cv/regenerate-sharecode")
def regenerate_sharecode(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    if cv.student_global_profile:
        cv.sharecode = employment.generate_sharecode(db, registration_number=cv.student_global_profile.global_student_number, first_name=cv.student_global_profile.first_name, last_name=cv.student_global_profile.last_name)
    else:
        identity = cv.external_identity or {}
        cv.sharecode = employment.generate_sharecode(db, first_name=identity.get("first_name"), last_name=identity.get("last_name"), external=True)
    audit.record_audit(db, action="employment.sharecode.regenerated", current_user=current_user, entity_type="student_cv", entity_id=cv.id)
    db.commit()
    return {"sharecode": cv.sharecode}


@router.post("/me/cv/work-history", response_model=schemas.StudentCVWorkHistoryResponse)
def add_work_history(payload: schemas.StudentCVWorkHistoryCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    row = models.StudentCVWorkHistory(student_cv_id=cv.id, **payload.model_dump())
    db.add(row)
    audit.record_audit(db, action="employment.cv.work_history.created", current_user=current_user, entity_type="student_cv", entity_id=cv.id)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/me/cv/work-history/{item_id}")
def delete_work_history(item_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    row = db.query(models.StudentCVWorkHistory).filter(models.StudentCVWorkHistory.id == item_id, models.StudentCVWorkHistory.student_cv_id == cv.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Experience introuvable.")
    if row.locked:
        raise HTTPException(status_code=403, detail="Experience verrouillee ou verifiee.")
    db.delete(row)
    audit.record_audit(db, action="employment.cv.work_history.deleted", current_user=current_user, entity_type="student_cv", entity_id=cv.id, details={"item_id": item_id})
    db.commit()
    return {"status": "deleted"}


@router.get("/recruiter/jobs", response_model=list[schemas.JobOfferResponse])
def recruiter_jobs(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    return db.query(models.JobOffer).filter(models.JobOffer.recruiter_id == recruiter.id).order_by(models.JobOffer.created_at.desc()).all()


@router.post("/recruiter/jobs", response_model=schemas.JobOfferResponse)
def create_job(payload: schemas.JobOfferCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    _require_recruiter_payment(recruiter)
    count = db.query(models.JobOffer).filter(models.JobOffer.recruiter_id == recruiter.id, models.JobOffer.status != "archived").count()
    if recruiter.offers_allowed and count >= recruiter.offers_allowed:
        raise HTTPException(status_code=402, detail="Limite d'offres atteinte pour votre abonnement.")
    row = models.JobOffer(recruiter_id=recruiter.id, **payload.model_dump())
    db.add(row)
    audit.record_audit(db, action="employment.job_offer.created", current_user=current_user, entity_type="job_offer", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.put("/recruiter/jobs/{job_id}", response_model=schemas.JobOfferResponse)
def update_job(job_id: int, payload: schemas.JobOfferUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    _require_recruiter_payment(recruiter)
    row = db.query(models.JobOffer).filter(models.JobOffer.id == job_id, models.JobOffer.recruiter_id == recruiter.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Offre introuvable.")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(row, key, value)
    audit.record_audit(db, action="employment.job_offer.updated", current_user=current_user, entity_type="job_offer", entity_id=row.id, details={"fields": sorted(updates.keys())})
    db.commit()
    db.refresh(row)
    return row


@router.delete("/recruiter/jobs/{job_id}")
def delete_or_archive_job(job_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    _require_recruiter_payment(recruiter)
    row = db.query(models.JobOffer).filter(models.JobOffer.id == job_id, models.JobOffer.recruiter_id == recruiter.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Offre introuvable.")
    if db.query(models.JobApplication.id).filter(models.JobApplication.job_offer_id == row.id).first():
        row.status = "archived"
        action = "employment.job_offer.archived"
    else:
        db.delete(row)
        action = "employment.job_offer.deleted"
    audit.record_audit(db, action=action, current_user=current_user, entity_type="job_offer", entity_id=job_id)
    db.commit()
    return {"status": "archived" if action.endswith("archived") else "deleted"}


@router.post("/jobs/{job_id}/apply", response_model=schemas.JobApplicationResponse)
def apply_to_job(job_id: int, payload: schemas.JobApplicationCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    job = db.query(models.JobOffer).filter(models.JobOffer.id == job_id, models.JobOffer.status == "published").first()
    if not job:
        raise HTTPException(status_code=404, detail="Offre indisponible.")
    row = models.JobApplication(
        student_cv_id=cv.id,
        job_offer_id=job.id,
        motivation_message=payload.motivation_message,
        attached_documents=payload.attached_documents,
        status_history=[{"status": "submitted", "at": _now().isoformat()}],
    )
    db.add(row)
    audit.record_audit(db, action="employment.application.submitted", current_user=current_user, entity_type="job_offer", entity_id=job.id)
    db.commit()
    db.refresh(row)
    return row


@router.get("/me/applications", response_model=list[schemas.JobApplicationResponse])
def my_applications(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    return db.query(models.JobApplication).filter(models.JobApplication.student_cv_id == cv.id).order_by(models.JobApplication.created_at.desc()).all()


@router.get("/recruiter/applications", response_model=list[schemas.JobApplicationResponse])
def recruiter_applications(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    _require_recruiter_payment(recruiter)
    return db.query(models.JobApplication).join(models.JobOffer).filter(models.JobOffer.recruiter_id == recruiter.id).order_by(models.JobApplication.created_at.desc()).all()


@router.post("/recruiter/interviews", response_model=schemas.JobInterviewResponse)
def create_interview(payload: schemas.JobInterviewCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    _require_recruiter_payment(recruiter)
    application = db.query(models.JobApplication).join(models.JobOffer).filter(
        models.JobApplication.id == payload.job_application_id,
        models.JobOffer.recruiter_id == recruiter.id,
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Candidature introuvable.")
    application.status = "interview_invited"
    application.status_history = (application.status_history or []) + [{"status": "interview_invited", "at": _now().isoformat()}]
    row = models.JobInterview(
        recruiter_id=recruiter.id,
        student_cv_id=application.student_cv_id,
        job_application_id=application.id,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        mode=payload.mode,
        location_or_link=payload.location_or_link,
        note=payload.note,
    )
    db.add(row)
    audit.record_audit(db, action="employment.interview.invited", current_user=current_user, entity_type="job_application", entity_id=application.id)
    db.commit()
    db.refresh(row)
    return row


@router.get("/me/interviews", response_model=list[schemas.JobInterviewResponse])
def my_interviews(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    return db.query(models.JobInterview).filter(models.JobInterview.student_cv_id == cv.id).order_by(models.JobInterview.scheduled_at.desc()).all()


@router.post("/interviews/{interview_id}/respond")
def respond_interview(interview_id: int, status: str, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    if status not in {"accepted", "declined", "rescheduled"}:
        raise HTTPException(status_code=400, detail="Statut non valide.")
    cv = _student_cv_for_user(db, current_user)
    row = db.query(models.JobInterview).filter(models.JobInterview.id == interview_id, models.JobInterview.student_cv_id == cv.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Entretien introuvable.")
    row.status = status
    audit.record_audit(db, action="employment.interview.responded", current_user=current_user, entity_type="job_interview", entity_id=row.id, details={"status": status})
    db.commit()
    return {"status": row.status}
