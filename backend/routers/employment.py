from __future__ import annotations

import re
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from .. import audit, database, models, schemas, security
from ..services import ai_service, employment, file_storage

router = APIRouter(prefix="/employment", tags=["TeducAI Emploi"])
logger = logging.getLogger(__name__)
IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}


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
            "where t.typname = 'userrole' and e.enumlabel = 'RECRUITER'"
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
        "academic_credentials": cv.academic_credentials or [],
        "certificates": cv.certificates or [],
        "skills": cv.skills or [],
        "detailed_skills": cv.detailed_skills or [],
        "languages": cv.languages or [],
        "portfolio": cv.portfolio or [],
        "availability": cv.availability,
        "desired_location": cv.desired_location,
        "total_experience_years": cv.total_experience_years or employment.calculate_experience_years(cv),
        "external_identity": cv.external_identity,
        "work_history": cv.work_history,
        "created_at": cv.created_at,
        "updated_at": cv.updated_at,
    }


def _active_file_response(row: models.SecureFile):
    if row.storage_backend in {"s3", "minio"}:
        url = file_storage.signed_download_url(row.storage_backend, row.storage_path, row.content_type, row.original_filename)
        if url:
            return RedirectResponse(url)
    return FileResponse(file_storage.open_stored_file(row.storage_path), media_type=row.content_type)


async def _store_employment_image(
    upload: UploadFile,
    *,
    current_user: models.User,
    db: Session,
    entity_type: str,
    entity_id: str,
    display_name: str,
    folder: str,
) -> models.SecureFile:
    if upload.content_type not in IMAGE_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Image JPG, PNG ou WebP requise.")
    metadata = await file_storage.store_upload(
        upload,
        current_user.school_id,
        document_name=display_name,
        user_id=current_user.id,
        folder=folder,
    )
    db.query(models.SecureFile).filter(
        models.SecureFile.entity_type == entity_type,
        models.SecureFile.entity_id == entity_id,
        models.SecureFile.status == "active",
    ).update({"status": "deleted", "deleted_at": _now()}, synchronize_session=False)
    row = models.SecureFile(
        **metadata,
        category=entity_type,
        visibility="public",
        is_shareable=True,
        approval_status="approved",
        approved_by_id=current_user.id,
        approved_at=_now(),
        entity_type=entity_type,
        entity_id=entity_id,
        school_id=current_user.school_id,
        uploaded_by_id=current_user.id,
    )
    db.add(row)
    db.flush()
    return row


def _latest_employment_file(db: Session, entity_type: str, entity_id: str) -> models.SecureFile:
    row = db.query(models.SecureFile).filter(
        models.SecureFile.entity_type == entity_type,
        models.SecureFile.entity_id == entity_id,
        models.SecureFile.status == "active",
    ).order_by(models.SecureFile.created_at.desc(), models.SecureFile.id.desc()).first()
    if not row:
        raise HTTPException(status_code=404, detail="Image introuvable.")
    return row


def _job_response(row: models.JobOffer) -> dict:
    payload = schemas.JobOfferResponse.model_validate(row).model_dump()
    payload["recruiter_logo_url"] = row.recruiter.logo_url if row.recruiter else None
    payload["company_logo_url"] = row.recruiter.logo_url if row.recruiter else None
    return payload


@router.get("/sectors")
def sectors():
    return {"sectors": employment.SECTORS}


@router.get("/jobs", response_model=list[schemas.JobOfferResponse])
def public_jobs(sector: str | None = None, db: Session = Depends(database.get_db)):
    now = _now()
    db.query(models.JobOffer).filter(models.JobOffer.deadline.isnot(None), models.JobOffer.deadline < now, models.JobOffer.status == "published").update({"status": "expired"}, synchronize_session=False)
    db.commit()
    query = db.query(models.JobOffer).filter(models.JobOffer.status == "published")
    if sector:
        query = query.filter(models.JobOffer.sector.ilike(f"%{sector}%"))
    return [_job_response(row) for row in query.order_by(models.JobOffer.created_at.desc()).limit(100).all()]


@router.get("/skill-categories")
def skill_categories():
    return {"categories": employment.SKILL_CATEGORIES}


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


@router.post("/recruiter/sharecode/lookup")
def recruiter_lookup_sharecode(payload: schemas.SharecodeLookup, request: Request, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    _require_recruiter_payment(recruiter)
    result = lookup_sharecode(payload, request, db)
    recruiter.cv_views_used += 1
    db.commit()
    return {**result, "ai_score": 82, "recruiter_views_used": recruiter.cv_views_used}


@router.get("/cv/{cv_id}/photo")
def get_cv_photo(cv_id: int, db: Session = Depends(database.get_db)):
    cv = db.query(models.StudentCV).filter(models.StudentCV.id == cv_id, models.StudentCV.share_enabled == True).first()  # noqa: E712
    if not cv:
        raise HTTPException(status_code=404, detail="Photo introuvable.")
    return _active_file_response(_latest_employment_file(db, "employment_cv_photo", str(cv.id)))


@router.get("/recruiters/{recruiter_id}/logo")
def get_recruiter_logo(recruiter_id: int, db: Session = Depends(database.get_db)):
    recruiter = db.query(models.RecruiterProfile).filter(models.RecruiterProfile.id == recruiter_id, models.RecruiterProfile.is_active == True).first()  # noqa: E712
    if not recruiter:
        raise HTTPException(status_code=404, detail="Logo introuvable.")
    return _active_file_response(_latest_employment_file(db, "employment_recruiter_logo", str(recruiter.id)))


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
    days_remaining = None
    if recruiter.subscription_expires_at:
        expires = recruiter.subscription_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        days_remaining = max((expires - _now()).days, 0)
    return {
        "id": recruiter.id,
        "company_name": recruiter.company_name,
        "contact_name": recruiter.contact_name,
        "sector": recruiter.sector,
        "phone": recruiter.phone,
        "website": recruiter.website,
        "logo_url": recruiter.logo_url,
        "company_description": recruiter.company_description,
        "subscription_plan": recruiter.subscription_plan,
        "subscription_duration_months": recruiter.subscription_duration_months,
        "subscription_expires_at": recruiter.subscription_expires_at,
        "auto_renew": recruiter.auto_renew,
        "days_remaining": days_remaining,
        "payment_status": recruiter.payment_status,
        "ai_credits_balance": recruiter.ai_credits_balance,
        "offers_allowed": recruiter.offers_allowed,
        "cv_views_allowed": recruiter.cv_views_allowed,
    }


@router.put("/recruiter/profile")
def update_recruiter_profile(payload: schemas.RecruiterProfileUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(recruiter, key, value)
    audit.record_audit(db, action="employment.recruiter.profile_updated", current_user=current_user, entity_type="recruiter_profile", entity_id=recruiter.id, details={"fields": sorted(updates.keys())})
    db.commit()
    return recruiter_me(current_user, db)


@router.post("/recruiter/logo")
async def upload_recruiter_logo(
    logo: UploadFile = File(...),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    recruiter = _recruiter_for_user(db, current_user)
    row = await _store_employment_image(
        logo,
        current_user=current_user,
        db=db,
        entity_type="employment_recruiter_logo",
        entity_id=str(recruiter.id),
        display_name=f"Logo {recruiter.company_name}",
        folder="employment/recruiters",
    )
    recruiter.logo_url = f"/employment/recruiters/{recruiter.id}/logo"
    audit.record_audit(db, action="employment.recruiter.logo_updated", current_user=current_user, entity_type="recruiter_profile", entity_id=recruiter.id, details={"file_id": row.id})
    db.commit()
    return recruiter_me(current_user, db)


@router.delete("/recruiter/logo", status_code=status.HTTP_204_NO_CONTENT)
def delete_recruiter_logo(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    recruiter.logo_url = None
    db.query(models.SecureFile).filter(
        models.SecureFile.entity_type == "employment_recruiter_logo",
        models.SecureFile.entity_id == str(recruiter.id),
        models.SecureFile.status == "active",
    ).update({"status": "deleted", "deleted_at": _now()}, synchronize_session=False)
    audit.record_audit(db, action="employment.recruiter.logo_deleted", current_user=current_user, entity_type="recruiter_profile", entity_id=recruiter.id)
    db.commit()


@router.post("/recruiter/subscription")
def update_recruiter_subscription(payload: schemas.RecruiterSubscriptionUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    recruiter.subscription_plan = payload.plan
    recruiter.subscription_duration_months = payload.duration_months
    recruiter.auto_renew = payload.auto_renew
    recruiter.subscription_started_at = _now()
    recruiter.subscription_expires_at = _now() + timedelta(days=payload.duration_months * 30)
    recruiter.payment_status = "confirmed" if payload.payment_provider == "free" else "pending"
    payment = models.PlatformPayment(
        reference=f"EMP-SUB-{recruiter.id}-{int(_now().timestamp())}",
        payer_user_id=current_user.id,
        payment_type="employment_recruiter_subscription_renewal",
        amount=0,
        currency="FCFA",
        provider=payload.payment_provider,
        status=recruiter.payment_status,
        beneficiary_entity="platform",
        metadata_json={"module": "teducai_emploi", "plan": payload.plan, "duration_months": payload.duration_months, "auto_renew": payload.auto_renew},
    )
    db.add(payment)
    audit.record_audit(db, action="employment.recruiter.subscription_updated", current_user=current_user, entity_type="recruiter_profile", entity_id=recruiter.id)
    db.commit()
    return recruiter_me(current_user, db)


@router.post("/recruiter/ai-credits")
def purchase_recruiter_ai_credits(payload: schemas.EmploymentAICreditPurchase, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    status = "confirmed" if payload.payment_provider == "free" else "pending"
    if status == "confirmed":
        recruiter.ai_credits_balance += payload.credits
    db.add(models.PlatformPayment(
        reference=f"EMP-AI-{recruiter.id}-{int(_now().timestamp())}",
        payer_user_id=current_user.id,
        payment_type="employment_ai_credits",
        amount=0,
        currency="FCFA",
        provider=payload.payment_provider,
        status=status,
        beneficiary_entity="platform",
        credits_amount=payload.credits,
        metadata_json={"module": "teducai_emploi", "target": "recruiter"},
    ))
    db.commit()
    return {"status": status, "ai_credits_balance": recruiter.ai_credits_balance, "credits_requested": payload.credits}


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
    cv.total_experience_years = employment.calculate_experience_years(cv)
    audit.record_audit(db, action="employment.cv.updated", current_user=current_user, entity_type="student_cv", entity_id=cv.id, details={"fields": sorted(updates.keys())})
    db.commit()
    db.refresh(cv)
    return _cv_response(cv)


@router.post("/me/cv/photo")
async def upload_my_cv_photo(
    photo: UploadFile = File(...),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    cv = _student_cv_for_user(db, current_user)
    row = await _store_employment_image(
        photo,
        current_user=current_user,
        db=db,
        entity_type="employment_cv_photo",
        entity_id=str(cv.id),
        display_name=f"Photo CV {cv.sharecode}",
        folder="employment/cv",
    )
    cv.cv_photo_url = f"/employment/cv/{cv.id}/photo"
    audit.record_audit(db, action="employment.cv.photo_updated", current_user=current_user, entity_type="student_cv", entity_id=cv.id, details={"file_id": row.id})
    db.commit()
    db.refresh(cv)
    return _cv_response(cv)


@router.delete("/me/cv/photo", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_cv_photo(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    cv.cv_photo_url = None
    db.query(models.SecureFile).filter(
        models.SecureFile.entity_type == "employment_cv_photo",
        models.SecureFile.entity_id == str(cv.id),
        models.SecureFile.status == "active",
    ).update({"status": "deleted", "deleted_at": _now()}, synchronize_session=False)
    audit.record_audit(db, action="employment.cv.photo_deleted", current_user=current_user, entity_type="student_cv", entity_id=cv.id)
    db.commit()


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
    db.flush()
    cv.total_experience_years = employment.calculate_experience_years(cv)
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
    return [_job_response(row) for row in db.query(models.JobOffer).filter(models.JobOffer.recruiter_id == recruiter.id).order_by(models.JobOffer.created_at.desc()).all()]


@router.post("/recruiter/jobs", response_model=schemas.JobOfferResponse)
def create_job(payload: schemas.JobOfferCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    _require_recruiter_payment(recruiter)
    count = db.query(models.JobOffer).filter(models.JobOffer.recruiter_id == recruiter.id, models.JobOffer.status != "archived").count()
    if recruiter.offers_allowed and count >= recruiter.offers_allowed:
        raise HTTPException(status_code=402, detail="Limite d'offres atteinte pour votre abonnement.")
    row = models.JobOffer(recruiter_id=recruiter.id, **payload.model_dump())
    db.add(row)
    db.flush()
    matches = employment.candidate_matches(db, row, limit=10)
    row.ai_match_summary = {"top_candidates": matches, "generated_at": _now().isoformat()}
    db.add(models.EmploymentNotification(audience="recruiter", recruiter_id=recruiter.id, title="Matching IA disponible", message=f"{len(matches)} candidats ont ete classes pour l'offre {row.title}.", payload={"job_offer_id": row.id}))
    for item in matches[:5]:
        db.add(models.EmploymentNotification(audience="student", student_cv_id=item["cv"]["id"], title="Offre recommandee", message=f"Une offre correspond a votre profil: {row.title}.", payload={"job_offer_id": row.id, "score": item["score"]}))
    audit.record_audit(db, action="employment.job_offer.created", current_user=current_user, entity_type="job_offer", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return _job_response(row)


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
    return _job_response(row)


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
        ai_match_score=employment.match_score(job, cv)["score"],
        ai_match_details=employment.match_score(job, cv),
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


@router.get("/me/recommended-jobs")
def my_recommended_jobs(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    return [
        {"job": _job_response(item["job"]), "score": item["score"], "details": item["details"]}
        for item in employment.recommended_jobs(db, cv, limit=20)
    ]


@router.post("/me/ai-credits")
def purchase_student_ai_credits(payload: schemas.EmploymentAICreditPurchase, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    cv = _student_cv_for_user(db, current_user)
    status = "confirmed" if payload.payment_provider == "free" else "pending"
    db.add(models.PlatformPayment(
        reference=f"EMP-STU-AI-{current_user.id}-{int(_now().timestamp())}",
        payer_user_id=current_user.id,
        payment_type="employment_student_ai_credits",
        amount=0,
        currency="FCFA",
        provider=payload.payment_provider,
        status=status,
        beneficiary_entity="platform",
        credits_amount=payload.credits,
        metadata_json={"module": "teducai_emploi", "student_cv_id": cv.id},
    ))
    db.commit()
    return {"status": status, "credits_requested": payload.credits}


@router.get("/recruiter/applications", response_model=list[schemas.JobApplicationResponse])
def recruiter_applications(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    _require_recruiter_payment(recruiter)
    return db.query(models.JobApplication).join(models.JobOffer).filter(models.JobOffer.recruiter_id == recruiter.id).order_by(models.JobApplication.created_at.desc()).all()


@router.get("/recruiter/jobs/{job_id}/matches")
def recruiter_job_matches(job_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    recruiter = _recruiter_for_user(db, current_user)
    _require_recruiter_payment(recruiter)
    job = db.query(models.JobOffer).filter(models.JobOffer.id == job_id, models.JobOffer.recruiter_id == recruiter.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Offre introuvable.")
    matches = employment.candidate_matches(db, job, limit=25)
    job.ai_match_summary = {"top_candidates": matches, "generated_at": _now().isoformat()}
    db.commit()
    return {"job_id": job.id, "matches": matches}


@router.post("/agent")
def employment_agent(payload: schemas.EmploymentAgentRequest, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    context = {"role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role), "module": "teducai_emploi", "mode": payload.mode}
    response = ai_service.ai_service.generate_response_from_config(payload.prompt, context, db)
    return {
        "type": "content",
        "message": response.get("message"),
        "data": response.get("data") or {
            "tables": [{"title": "Resultats Emploi", "rows": []}],
            "statistics": {"profils_analyses": db.query(models.StudentCV).count(), "offres_actives": db.query(models.JobOffer).filter(models.JobOffer.status == "published").count()},
            "recommendations": ["Affinez les competences et langues pour ameliorer le matching.", "Utilisez les ShareCodes pour consulter les profils autorises."],
        },
    }


@router.get("/admin/overview")
def employment_admin_overview(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Admin requis.")
    total_revenue = db.query(func.coalesce(func.sum(models.PlatformPayment.amount), 0)).filter(models.PlatformPayment.payment_type.ilike("employment%")).scalar() or 0
    recruiters = db.query(models.RecruiterProfile).order_by(models.RecruiterProfile.created_at.desc()).limit(50).all()
    jobs = db.query(models.JobOffer).order_by(models.JobOffer.created_at.desc()).limit(50).all()
    notifications = db.query(models.EmploymentNotification).order_by(models.EmploymentNotification.created_at.desc()).limit(50).all()
    return {
        "stats": {
            "recruiters": db.query(models.RecruiterProfile).count(),
            "active_students": db.query(models.StudentCV).filter(models.StudentCV.looking_for_job == True).count(),  # noqa: E712
            "published_jobs": db.query(models.JobOffer).filter(models.JobOffer.status == "published").count(),
            "expired_jobs": db.query(models.JobOffer).filter(models.JobOffer.status == "expired").count(),
            "applications": db.query(models.JobApplication).count(),
            "subscription_revenue": float(total_revenue),
            "ai_credit_revenue": float(total_revenue),
        },
        "recruiters": [
            {
                "id": row.id,
                "company_name": row.company_name,
                "contact_name": row.contact_name,
                "payment_status": row.payment_status,
                "subscription_plan": row.subscription_plan,
                "ai_credits_balance": row.ai_credits_balance,
                "is_active": row.is_active,
            }
            for row in recruiters
        ],
        "students": [employment.public_cv_payload(cv) for cv in db.query(models.StudentCV).order_by(models.StudentCV.updated_at.desc()).limit(50).all()],
        "jobs": [
            {
                "id": row.id,
                "title": row.title,
                "company": row.company,
                "sector": row.sector,
                "status": row.status,
                "applications": len(row.applications),
            }
            for row in jobs
        ],
        "notifications": [
            {"id": row.id, "audience": row.audience, "title": row.title, "message": row.message, "created_at": row.created_at}
            for row in notifications
        ],
    }


@router.post("/admin/notifications")
def employment_admin_notification(payload: schemas.EmploymentNotificationCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Admin requis.")
    row = models.EmploymentNotification(created_by_id=current_user.id, **payload.model_dump())
    db.add(row)
    audit.record_audit(db, action="employment.notification.created", current_user=current_user, entity_type="employment_notification")
    db.commit()
    return {"status": "sent", "id": row.id}


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
