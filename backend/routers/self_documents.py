"""Self-service administrative documents (automation B).

Students (and parents, for their linked children) generate certificats de
scolarité, attestations de fréquentation and payment receipts on request —
no staff involvement. Documents are recorded in the existing
``GeneratedDocument`` table (``source_type="self_service"``) with the full
render payload in ``content`` under a unique reference, so each document can
be re-displayed identically and verified. Rendering is print-friendly HTML
on the frontend (PDF export stays on the NOT-READY list)."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import audit, database, models, security

router = APIRouter(prefix="/self-documents", tags=["Self-service documents"])

STUDENT_ROLES = (models.UserRole.STUDENT, models.UserRole.PUPIL)
ADMIN_ROLES = (models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION, models.UserRole.SECRETARY, models.UserRole.REGISTRAR)
DOC_PREFIX = {"certificate": "CERT", "attestation": "ATT", "receipt": "REC"}
DOC_TYPE_ENUM = {
    "certificate": models.GeneratedDocumentType.CERTIFICATE,
    "attestation": models.GeneratedDocumentType.OTHER,
    "receipt": models.GeneratedDocumentType.RECEIPT,
}
DOC_TITLE = {
    "certificate": "Certificat de scolarité",
    "attestation": "Attestation de fréquentation",
    "receipt": "Reçu de paiement",
}
SOURCE_TYPE = "self_service"


def _resolve_student(db: Session, current_user: models.User, student_id: Optional[int]) -> models.StudentProfile:
    """Who may generate for whom: a student for themselves; a parent for a
    linked child; school staff for any student of their school."""
    if current_user.role in STUDENT_ROLES:
        profile = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil élève introuvable.")
        return profile
    if current_user.role == models.UserRole.PARENT:
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id requis pour un parent.")
        link = db.query(models.ParentStudentLink).filter(
            models.ParentStudentLink.parent_user_id == current_user.id,
            models.ParentStudentLink.student_id == student_id,
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="Cet élève n'est pas rattaché à votre compte.")
        profile = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil élève introuvable.")
        return profile
    if current_user.role in ADMIN_ROLES:
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id requis.")
        profile = db.query(models.StudentProfile).join(models.User, models.User.id == models.StudentProfile.user_id).filter(
            models.StudentProfile.id == student_id,
        ).first()
        if not profile or (current_user.role != models.UserRole.SUPER_ADMIN and profile.user and profile.user.school_id != current_user.school_id):
            raise HTTPException(status_code=404, detail="Profil élève introuvable dans votre établissement.")
        return profile
    raise HTTPException(status_code=403, detail="Accès refusé.")


def _school_for(db: Session, profile: models.StudentProfile) -> models.School:
    school_id = profile.user.school_id if profile.user else None
    school = db.query(models.School).filter(models.School.id == school_id).first() if school_id else None
    if not school:
        raise HTTPException(status_code=409, detail="Établissement introuvable pour cet élève.")
    return school


def _current_year(db: Session, school: models.School) -> Optional[models.AcademicYear]:
    return db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id == school.id,
        models.AcademicYear.is_current == True,  # noqa: E712
    ).first()


def _enrollment_context(db: Session, profile: models.StudentProfile, school: models.School) -> dict:
    class_name, level = None, None
    if profile.current_class_id:
        cls = db.query(models.Class).filter(models.Class.id == profile.current_class_id).first()
        if cls:
            class_name, level = cls.name, cls.level
    year = _current_year(db, school)
    return {"class_name": class_name, "level": level, "academic_year": year.name if year else None}


def _base_payload(db: Session, profile: models.StudentProfile, school: models.School, doc_type: str) -> dict:
    reference = f"{DOC_PREFIX[doc_type]}-{uuid.uuid4().hex[:10].upper()}"
    return {
        "reference": reference,
        "doc_type": doc_type,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "school": {"name": school.name, "address": school.address, "phone": school.phone, "email": school.email, "logo_url": school.logo_url},
        "student": {
            "full_name": profile.user.full_name if profile.user else None,
            "registration_number": profile.registration_number,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "gender": profile.gender,
        },
        "enrollment": _enrollment_context(db, profile, school),
    }


def _store(db: Session, payload: dict, profile: models.StudentProfile, school: models.School, current_user: models.User, source_id: Optional[int] = None) -> dict:
    doc_type = payload["doc_type"]
    year = _current_year(db, school)
    db.add(models.GeneratedDocument(
        document_type=DOC_TYPE_ENUM[doc_type],
        title=DOC_TITLE[doc_type],
        reference=payload["reference"],
        source_type=SOURCE_TYPE,
        source_id=source_id,
        student_id=profile.id,
        parent_user_id=current_user.id if current_user.role == models.UserRole.PARENT else None,
        school_id=school.id,
        academic_year_id=year.id if year else None,
        content=payload,
        generated_by_id=current_user.id,
    ))
    audit.record_audit(db, action=f"self_document.{doc_type}.generated", current_user=current_user, entity_type="generated_document", entity_id=payload["reference"])
    db.commit()
    return payload


@router.get("/children")
def my_children(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)) -> List[dict]:
    """Students the current user may generate documents for (self, or linked children)."""
    profiles: List[models.StudentProfile] = []
    if current_user.role in STUDENT_ROLES:
        profile = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
        if profile:
            profiles = [profile]
    elif current_user.role == models.UserRole.PARENT:
        links = db.query(models.ParentStudentLink).filter(models.ParentStudentLink.parent_user_id == current_user.id).all()
        ids = [link.student_id for link in links]
        if ids:
            profiles = db.query(models.StudentProfile).filter(models.StudentProfile.id.in_(ids)).all()
    return [
        {"student_id": p.id, "full_name": p.user.full_name if p.user else None, "registration_number": p.registration_number}
        for p in profiles
    ]


@router.post("/certificate")
def generate_certificate(student_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Certificat de scolarité — proves current enrollment."""
    profile = _resolve_student(db, current_user, student_id)
    school = _school_for(db, profile)
    return _store(db, _base_payload(db, profile, school, "certificate"), profile, school, current_user)


@router.post("/attestation")
def generate_attestation(student_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Attestation de fréquentation — same facts, attendance-oriented wording."""
    profile = _resolve_student(db, current_user, student_id)
    school = _school_for(db, profile)
    return _store(db, _base_payload(db, profile, school, "attestation"), profile, school, current_user)


@router.get("/my-payments")
def my_payments(student_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Successful payments of the resolved student, for receipt generation."""
    profile = _resolve_student(db, current_user, student_id)
    rows = (
        db.query(models.Payment, models.Fee)
        .join(models.Fee, models.Fee.id == models.Payment.fee_id)
        .filter(models.Fee.student_id == profile.id, models.Payment.status == "successful")
        .order_by(models.Payment.id.desc())
        .limit(100)
        .all()
    )
    return [
        {"payment_id": payment.id, "fee_title": fee.title, "amount": payment.amount,
         "payment_date": payment.payment_date, "method": payment.payment_method,
         "receipt_number": payment.receipt_number}
        for payment, fee in rows
    ]


@router.post("/receipt/{payment_id}")
def generate_receipt(payment_id: int, student_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Receipt for one of the student's successful payments."""
    profile = _resolve_student(db, current_user, student_id)
    school = _school_for(db, profile)
    row = (
        db.query(models.Payment, models.Fee)
        .join(models.Fee, models.Fee.id == models.Payment.fee_id)
        .filter(models.Payment.id == payment_id, models.Fee.student_id == profile.id, models.Payment.status == "successful")
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Paiement introuvable pour cet élève.")
    payment, fee = row
    payload = _base_payload(db, profile, school, "receipt")
    paid_total = sum(p.amount for p in (fee.payments or []) if (p.status or "successful") == "successful")
    payload["payment"] = {
        "payment_id": payment.id, "fee_title": fee.title, "amount": payment.amount,
        "method": payment.payment_method, "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
        "receipt_number": payment.receipt_number, "fee_amount": fee.amount,
        "outstanding_after": round(max(fee.amount - paid_total, 0), 2),
    }
    return _store(db, payload, profile, school, current_user, source_id=payment.id)


@router.get("/mine")
def my_documents(student_id: Optional[int] = None, limit: int = Query(50, ge=1, le=200), db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    profile = _resolve_student(db, current_user, student_id)
    rows = (
        db.query(models.GeneratedDocument)
        .filter(
            models.GeneratedDocument.student_id == profile.id,
            models.GeneratedDocument.source_type == SOURCE_TYPE,
        )
        .order_by(models.GeneratedDocument.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {"id": r.id, "reference": r.reference, "doc_type": (r.content or {}).get("doc_type"),
         "title": r.title, "created_at": r.generated_at, "payload": r.content}
        for r in rows
    ]


@router.get("/verify/{reference}")
def verify_document(reference: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Authenticity check by reference (any authenticated user)."""
    row = db.query(models.GeneratedDocument).filter(
        models.GeneratedDocument.reference == reference,
        models.GeneratedDocument.source_type == SOURCE_TYPE,
    ).first()
    if not row:
        return {"valid": False}
    payload = row.content or {}
    return {
        "valid": True, "doc_type": payload.get("doc_type"), "issued_at": row.generated_at,
        "school_name": (payload.get("school") or {}).get("name"),
        "student_name": (payload.get("student") or {}).get("full_name"),
    }
