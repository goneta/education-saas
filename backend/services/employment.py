from __future__ import annotations

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import audit, models


DEFAULT_PRIVACY = {
    "visible_via_sharecode": True,
    "visible_in_sector_search": False,
    "show_detailed_grades": False,
    "show_averages": True,
    "show_teacher_comments": False,
    "show_behavior": False,
    "show_direct_contact": False,
}

SECTORS = [
    "Informatique",
    "Commerce",
    "Electricite",
    "Maintenance industrielle",
    "Mecanique",
    "Cuisine",
    "Gestion",
    "Sante",
    "Education",
    "BTP",
    "Transport",
    "Administration",
    "Communication",
    "Agriculture",
    "Hotellerie",
    "Autre",
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _initials(first_name: str | None, last_name: str | None) -> str:
    first = (first_name or "").strip()[:1]
    last = (last_name or "").strip()[:1]
    value = f"{first}{last}".upper()
    return value or "CV"


def _external_student_number() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "STU" + "".join(secrets.choice(alphabet) for _ in range(10))


def generate_sharecode(
    db: Session,
    *,
    registration_number: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    external: bool = False,
) -> str:
    base = _external_student_number() if external or not registration_number else registration_number.strip().upper()
    prefix = f"{base}-{_initials(first_name, last_name)}"
    for attempt in range(20):
        value = prefix if attempt == 0 else f"{prefix}-{secrets.token_hex(2).upper()}"
        if not db.query(models.StudentCV.id).filter(models.StudentCV.sharecode == value).first():
            return value
    raise HTTPException(status_code=500, detail="Impossible de generer un sharecode unique.")


def ensure_student_cv(db: Session, global_profile: models.StudentGlobalProfile, *, current_user: models.User | None = None) -> models.StudentCV:
    row = db.query(models.StudentCV).filter(models.StudentCV.student_global_profile_id == global_profile.id).first()
    if row:
        return row
    registration_number = global_profile.student_profile.registration_number if global_profile.student_profile else None
    row = models.StudentCV(
        student_global_profile_id=global_profile.id,
        user_id=global_profile.user_id,
        sharecode=generate_sharecode(
            db,
            registration_number=registration_number or global_profile.global_student_number,
            first_name=global_profile.first_name,
            last_name=global_profile.last_name,
        ),
        professional_title="Etudiant",
        summary=None,
        sectors=[],
        looking_for_job=False,
        cv_photo_url=global_profile.photo_url,
        privacy_settings=dict(DEFAULT_PRIVACY),
        academic_timeline=[],
        skills=[],
        languages=[],
        portfolio=[],
    )
    db.add(row)
    db.flush()
    audit.record_audit(
        db,
        action="employment.cv.created",
        current_user=current_user,
        entity_type="student_cv",
        entity_id=row.id,
        details={"student_global_profile_id": global_profile.id, "automatic": True},
    )
    return row


def build_academic_snapshot(db: Session, global_profile: models.StudentGlobalProfile) -> list[dict[str, Any]]:
    rows = []
    enrollments = db.query(models.StudentEnrollment).filter(
        models.StudentEnrollment.student_global_profile_id == global_profile.id
    ).order_by(models.StudentEnrollment.start_date.desc(), models.StudentEnrollment.id.desc()).all()
    for enrollment in enrollments:
        grades = db.query(models.Grade).filter(models.Grade.student_enrollment_id == enrollment.id).all()
        numeric_grades = [grade.score for grade in grades if getattr(grade, "score", None) is not None]
        average = round(sum(numeric_grades) / len(numeric_grades), 2) if numeric_grades else None
        rows.append({
            "enrollment_id": enrollment.id,
            "school": enrollment.school.name if enrollment.school else None,
            "academic_year": enrollment.academic_year.name if enrollment.academic_year else None,
            "school_model": enrollment.school_model_assignment.school_model.name if enrollment.school_model_assignment and enrollment.school_model_assignment.school_model else None,
            "class": enrollment.class_.name if enrollment.class_ else None,
            "program": enrollment.program.name if enrollment.program else None,
            "enrollment_type": enrollment.enrollment_type,
            "schedule_type": enrollment.schedule_type,
            "average": average,
            "certifications_count": db.query(models.CertificateRequest).filter(models.CertificateRequest.student_enrollment_id == enrollment.id).count(),
            "internships_count": db.query(models.InternshipAssignment).filter(models.InternshipAssignment.student_enrollment_id == enrollment.id).count(),
            "locked": True,
        })
    return rows


def refresh_cv_from_academic_year(
    db: Session,
    *,
    academic_year_id: int,
    current_user: models.User,
) -> int:
    enrollments = db.query(models.StudentEnrollment).filter(
        models.StudentEnrollment.academic_year_id == academic_year_id
    ).all()
    count = 0
    for enrollment in enrollments:
        cv = ensure_student_cv(db, enrollment.student_global_profile, current_user=current_user)
        cv.academic_timeline = build_academic_snapshot(db, enrollment.student_global_profile)
        cv.last_auto_updated_at = _utcnow()
        count += 1
    audit.record_audit(
        db,
        action="employment.cv.academic_year_refreshed",
        current_user=current_user,
        entity_type="academic_year",
        entity_id=academic_year_id,
        details={"cv_count": count},
    )
    return count


def public_cv_payload(cv: models.StudentCV) -> dict[str, Any]:
    privacy = {**DEFAULT_PRIVACY, **(cv.privacy_settings or {})}
    profile = cv.student_global_profile
    name = None
    if profile:
        name = " ".join(part for part in [profile.first_name, profile.last_name] if part)
    elif cv.external_identity:
        name = " ".join(part for part in [cv.external_identity.get("first_name"), cv.external_identity.get("last_name")] if part)
    payload = {
        "id": cv.id,
        "name": name,
        "professional_title": cv.professional_title,
        "summary": cv.summary,
        "sectors": cv.sectors or [],
        "looking_for_job": cv.looking_for_job,
        "cv_photo_url": cv.cv_photo_url or (profile.photo_url if profile else None),
        "skills": cv.skills or [],
        "languages": cv.languages or [],
        "portfolio": cv.portfolio or [],
        "availability": cv.availability,
        "work_history": [
            {
                "id": item.id,
                "company": item.company,
                "sector": item.sector,
                "position": item.position,
                "experience_type": item.experience_type,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "current": item.current,
                "description": item.description,
                "missions": item.missions or [],
                "skills_used": item.skills_used or [],
                "verified_by_entity": item.verified_by_entity,
            }
            for item in cv.work_history
        ],
        "privacy_settings": privacy,
    }
    if privacy.get("show_averages") or privacy.get("show_detailed_grades"):
        payload["academic_timeline"] = cv.academic_timeline or []
    if privacy.get("show_direct_contact") and cv.user:
        payload["contact"] = {"email": cv.user.email, "phone": cv.user.phone_number}
    return payload


def rate_limit_sharecode(db: Session, *, ip_address: str | None) -> None:
    if not ip_address:
        return
    since = _utcnow() - timedelta(minutes=1)
    count = db.query(models.StudentCVAccessLog).filter(
        models.StudentCVAccessLog.ip_address == ip_address,
        models.StudentCVAccessLog.access_type == "sharecode_lookup",
        models.StudentCVAccessLog.created_at >= since,
    ).count()
    if count >= 20:
        raise HTTPException(status_code=429, detail="Trop de tentatives. Reessayez plus tard.")
