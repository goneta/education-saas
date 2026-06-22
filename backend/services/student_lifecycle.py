from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import audit, models
from . import school_context


ACTIVE_ENROLLMENT_STATUSES = {"active", "transferred_in"}
CONCURRENT_MODEL_CODES = {"TECHNICAL", "PROFESSIONAL", "VOCATIONAL"}
CONCURRENT_ENROLLMENT_TYPES = {
    "part_time",
    "module",
    "certification",
    "evening_course",
    "weekend_course",
    "internship",
}


@dataclass(frozen=True)
class StudentAccess:
    global_profile: models.StudentGlobalProfile
    enrollment: models.StudentEnrollment | None
    can_edit: bool
    can_view_finance: bool


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _split_name(full_name: str | None) -> tuple[str, str]:
    parts = (full_name or "Eleve").strip().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _global_number(db: Session) -> str:
    while True:
        value = f"TED-{_utcnow().year}-{secrets.token_hex(4).upper()}"
        if not db.query(models.StudentGlobalProfile.id).filter(
            models.StudentGlobalProfile.global_student_number == value
        ).first():
            return value


def ensure_academic_year_for_context(
    db: Session,
    *,
    school_id: int,
    school_model_assignment_id: int,
) -> models.AcademicYear:
    row = db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id == school_id,
        models.AcademicYear.school_model_assignment_id == school_model_assignment_id,
        models.AcademicYear.is_current == True,  # noqa: E712
    ).order_by(models.AcademicYear.id.desc()).first()
    if row:
        return row
    year = _utcnow().year
    row = models.AcademicYear(
        name=f"{year}-{year + 1}",
        start_date=datetime(year, 9, 1),
        end_date=datetime(year + 1, 7, 31),
        is_current=True,
        school_id=school_id,
        school_model_assignment_id=school_model_assignment_id,
    )
    db.add(row)
    db.flush()
    return row


def ensure_global_profile(
    db: Session,
    student_profile: models.StudentProfile,
) -> models.StudentGlobalProfile:
    row = db.query(models.StudentGlobalProfile).filter(
        models.StudentGlobalProfile.student_profile_id == student_profile.id
    ).first()
    if row:
        return row
    first_name, last_name = _split_name(student_profile.user.full_name if student_profile.user else None)
    row = models.StudentGlobalProfile(
        student_profile_id=student_profile.id,
        user_id=student_profile.user_id,
        global_student_number=_global_number(db),
        first_name=first_name,
        last_name=last_name,
        date_of_birth=student_profile.date_of_birth,
        gender=student_profile.gender,
    )
    db.add(row)
    db.flush()
    return row


def enrollment_for_context(
    db: Session,
    global_profile_id: int,
    *,
    school_id: int,
    school_model_assignment_id: int | None = None,
    academic_year_id: int | None = None,
    active_only: bool = False,
) -> models.StudentEnrollment | None:
    query = db.query(models.StudentEnrollment).filter(
        models.StudentEnrollment.student_global_profile_id == global_profile_id,
        models.StudentEnrollment.school_id == school_id,
    )
    if school_model_assignment_id:
        query = query.filter(
            models.StudentEnrollment.school_model_assignment_id == school_model_assignment_id
        )
    if academic_year_id:
        query = query.filter(models.StudentEnrollment.academic_year_id == academic_year_id)
    if active_only:
        query = query.filter(models.StudentEnrollment.enrollment_status.in_(ACTIVE_ENROLLMENT_STATUSES))
    return query.order_by(models.StudentEnrollment.id.desc()).first()


def active_enrollment_for_student_profile_id(
    db: Session,
    student_profile_id: int,
    *,
    school_id: int,
    school_model_assignment_id: int | None = None,
    academic_year_id: int | None = None,
) -> models.StudentEnrollment | None:
    profile = db.query(models.StudentGlobalProfile).filter(
        models.StudentGlobalProfile.student_profile_id == student_profile_id
    ).first()
    if not profile:
        legacy = db.query(models.StudentProfile).filter(
            (models.StudentProfile.id == student_profile_id)
            | (models.StudentProfile.user_id == student_profile_id)
        ).first()
        if not legacy:
            return None
        profile = ensure_global_profile(db, legacy)
    return enrollment_for_context(
        db,
        profile.id,
        school_id=school_id,
        school_model_assignment_id=school_model_assignment_id,
        academic_year_id=academic_year_id,
        active_only=True,
    )


def ensure_current_enrollment(
    db: Session,
    *,
    student_profile: models.StudentProfile,
    current_user: models.User,
    school_id: int,
    school_model_assignment_id: int,
    academic_year_id: int,
    class_id: int | None = None,
) -> models.StudentEnrollment:
    global_profile = ensure_global_profile(db, student_profile)
    existing = enrollment_for_context(
        db,
        global_profile.id,
        school_id=school_id,
        school_model_assignment_id=school_model_assignment_id,
        academic_year_id=academic_year_id,
    )
    if existing:
        return existing
    year = db.query(models.AcademicYear).filter(models.AcademicYear.id == academic_year_id).first()
    row = models.StudentEnrollment(
        student_global_profile_id=global_profile.id,
        organization_id=db.query(models.School.organization_id).filter(
            models.School.id == school_id
        ).scalar(),
        school_id=school_id,
        school_model_assignment_id=school_model_assignment_id,
        academic_year_id=academic_year_id,
        class_id=class_id or student_profile.current_class_id,
        enrollment_status="active",
        enrollment_type="full_time",
        schedule_type="morning",
        primary_enrollment=True,
        start_date=year.start_date if year and year.start_date else _utcnow(),
        end_date=year.end_date if year else None,
        created_by_user_id=current_user.id,
    )
    db.add(row)
    db.flush()
    return row


def _overlaps_days(left: Iterable[str] | None, right: Iterable[str] | None) -> bool:
    if not left or not right:
        return True
    return bool(set(left) & set(right))


def schedule_conflicts(
    db: Session,
    global_profile_id: int,
    *,
    academic_year_id: int,
    days_of_week: list[str] | None,
    start_time,
    end_time,
    exclude_enrollment_id: int | None = None,
) -> list[models.StudentEnrollment]:
    query = db.query(models.StudentEnrollment).filter(
        models.StudentEnrollment.student_global_profile_id == global_profile_id,
        models.StudentEnrollment.academic_year_id == academic_year_id,
        models.StudentEnrollment.enrollment_status.in_(ACTIVE_ENROLLMENT_STATUSES),
    )
    if exclude_enrollment_id:
        query = query.filter(models.StudentEnrollment.id != exclude_enrollment_id)
    conflicts = []
    for row in query.all():
        if not start_time or not end_time or not row.start_time or not row.end_time:
            continue
        if _overlaps_days(days_of_week, row.days_of_week) and start_time < row.end_time and end_time > row.start_time:
            conflicts.append(row)
    return conflicts


def validate_concurrent_enrollment(
    db: Session,
    *,
    global_profile_id: int,
    assignment: models.SchoolModelAssignment,
    academic_year_id: int,
    enrollment_type: str,
    allows_concurrent_enrollment: bool,
    days_of_week: list[str] | None,
    start_time,
    end_time,
    force: bool,
    override_reason: str | None,
    current_user: models.User,
) -> list[int]:
    active = db.query(models.StudentEnrollment).filter(
        models.StudentEnrollment.student_global_profile_id == global_profile_id,
        models.StudentEnrollment.academic_year_id == academic_year_id,
        models.StudentEnrollment.enrollment_status.in_(ACTIVE_ENROLLMENT_STATUSES),
    ).all()
    if not active:
        return []
    compatible = (
        assignment.school_model.code in CONCURRENT_MODEL_CODES
        or enrollment_type in CONCURRENT_ENROLLMENT_TYPES
    ) and allows_concurrent_enrollment
    conflicts = schedule_conflicts(
        db,
        global_profile_id,
        academic_year_id=academic_year_id,
        days_of_week=days_of_week,
        start_time=start_time,
        end_time=end_time,
    )
    if (not compatible or conflicts) and not force:
        detail = "Inscription active incompatible pour cette annee academique."
        if conflicts:
            detail = "Conflit d'horaires detecte avec une inscription active."
        raise HTTPException(
            status_code=409,
            detail={"message": detail, "conflicting_enrollment_ids": [row.id for row in conflicts]},
        )
    if (not compatible or conflicts) and force:
        if current_user.role != models.UserRole.SUPER_ADMIN and not override_reason:
            raise HTTPException(status_code=403, detail="Une justification est obligatoire pour forcer l'inscription.")
        audit.record_audit(
            db,
            action="student_enrollment.conflict_overridden",
            current_user=current_user,
            entity_type="student_global_profile",
            entity_id=global_profile_id,
            details={
                "reason": override_reason,
                "conflicting_enrollment_ids": [row.id for row in conflicts],
                "model_code": assignment.school_model.code,
            },
        )
    return [row.id for row in conflicts]


def has_active_edit_grant(
    db: Session,
    *,
    current_user: models.User,
    school_id: int,
    academic_year_id: int,
    student_global_profile_id: int | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
) -> models.HistoricalDataEditGrant | None:
    now = _utcnow()
    query = db.query(models.HistoricalDataEditGrant).filter(
        models.HistoricalDataEditGrant.school_id == school_id,
        models.HistoricalDataEditGrant.academic_year_id == academic_year_id,
        models.HistoricalDataEditGrant.is_active == True,  # noqa: E712
        models.HistoricalDataEditGrant.valid_from <= now,
        models.HistoricalDataEditGrant.valid_until >= now,
    )
    if student_global_profile_id:
        query = query.filter(
            (models.HistoricalDataEditGrant.student_global_profile_id == None)  # noqa: E711
            | (models.HistoricalDataEditGrant.student_global_profile_id == student_global_profile_id)
        )
    if resource_type:
        query = query.filter(
            (models.HistoricalDataEditGrant.resource_type == None)  # noqa: E711
            | (models.HistoricalDataEditGrant.resource_type == resource_type)
        )
    if resource_id:
        query = query.filter(
            (models.HistoricalDataEditGrant.resource_id == None)  # noqa: E711
            | (models.HistoricalDataEditGrant.resource_id == resource_id)
        )
    return query.order_by(models.HistoricalDataEditGrant.valid_until.desc()).first()


def ensure_academic_year_is_editable(
    db: Session,
    *,
    current_user: models.User,
    school_id: int,
    academic_year_id: int,
    school_model_assignment_id: int | None = None,
    student_global_profile_id: int | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
) -> None:
    row = db.query(models.AcademicYearLock).filter(
        models.AcademicYearLock.school_id == school_id,
        models.AcademicYearLock.academic_year_id == academic_year_id,
        (
            models.AcademicYearLock.school_model_assignment_id == school_model_assignment_id
            if school_model_assignment_id
            else True
        ),
    ).order_by(models.AcademicYearLock.id.desc()).first()
    if not row or row.status in {"open", "closing"}:
        return
    if current_user.role == models.UserRole.SUPER_ADMIN:
        return
    grant = has_active_edit_grant(
        db,
        current_user=current_user,
        school_id=school_id,
        academic_year_id=academic_year_id,
        student_global_profile_id=student_global_profile_id,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    if grant:
        grant.used_at = _utcnow()
        return
    audit.record_audit(
        db,
        action="academic_year.edit_blocked",
        current_user=current_user,
        entity_type=resource_type or "academic_year",
        entity_id=resource_id or academic_year_id,
        details={"academic_year_id": academic_year_id, "status": row.status},
    )
    raise HTTPException(status_code=423, detail="Cette annee academique est cloturee et disponible en lecture seule.")


def ensure_student_context_access(
    db: Session,
    *,
    current_user: models.User,
    global_profile_id: int,
    require_edit: bool = False,
    school_id: int | None = None,
) -> StudentAccess:
    profile = db.query(models.StudentGlobalProfile).options(
        joinedload(models.StudentGlobalProfile.student_profile).joinedload(models.StudentProfile.user)
    ).filter(models.StudentGlobalProfile.id == global_profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil global eleve introuvable.")
    target_school_id = school_id or current_user.school_id
    if current_user.role == models.UserRole.SUPER_ADMIN:
        enrollment = enrollment_for_context(db, profile.id, school_id=target_school_id) if target_school_id else None
        return StudentAccess(profile, enrollment, True, True)
    if current_user.role in {models.UserRole.STUDENT, models.UserRole.PUPIL}:
        if profile.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Acces au profil d'un autre eleve interdit.")
        enrollment = enrollment_for_context(db, profile.id, school_id=current_user.school_id)
        return StudentAccess(profile, enrollment, False, enrollment is not None)
    enrollment = enrollment_for_context(db, profile.id, school_id=target_school_id) if target_school_id else None
    if not enrollment:
        approved_transfer = db.query(models.StudentTransferRequest.id).filter(
            models.StudentTransferRequest.student_global_profile_id == profile.id,
            models.StudentTransferRequest.to_school_id == target_school_id,
            models.StudentTransferRequest.status.in_(["approved", "completed"]),
        ).first()
        if not approved_transfer:
            raise HTTPException(status_code=403, detail="Cet etablissement n'a pas acces au parcours de cet eleve.")
    if require_edit and (not enrollment or enrollment.school_id != target_school_id):
        raise HTTPException(status_code=403, detail="Modification limitee a l'inscription de votre etablissement.")
    return StudentAccess(profile, enrollment, bool(enrollment), bool(enrollment))


def ensure_financial_data_access(
    db: Session,
    *,
    current_user: models.User,
    enrollment: models.StudentEnrollment,
) -> None:
    if current_user.role == models.UserRole.SUPER_ADMIN:
        return
    if not school_context.user_can_access_school(db, current_user, enrollment.school):
        audit.record_audit(
            db,
            action="student_finance.access_denied",
            current_user=current_user,
            entity_type="student_enrollment",
            entity_id=enrollment.id,
            details={"owner_school_id": enrollment.school_id},
        )
        raise HTTPException(status_code=403, detail="Les donnees financieres restent privees a l'etablissement proprietaire.")


def ensure_transfer_access(
    db: Session,
    *,
    current_user: models.User,
    transfer: models.StudentTransferRequest,
) -> None:
    if current_user.role == models.UserRole.SUPER_ADMIN:
        return
    allowed_school_ids = {transfer.from_school_id, transfer.to_school_id}
    if not any(
        school_context.user_can_access_school(db, current_user, school)
        for school in db.query(models.School).filter(models.School.id.in_(allowed_school_ids)).all()
    ):
        raise HTTPException(status_code=403, detail="Transfert hors de votre perimetre.")
