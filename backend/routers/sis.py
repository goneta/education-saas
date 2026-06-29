"""Student Information System extensions — guardians, emergency contacts and
confidential medical records (Slice 2, Loop 2 gaps).

All access resolves the student's institution through the linked `User` account
and enforces tenant isolation; medical records are restricted to authorized staff.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(prefix="/sis", tags=["Student Information System"])

ADMIN_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.REGISTRAR,
}
# Medical data is more sensitive than demographic data.
MEDICAL_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _student_in_school(db: Session, student_id: int, school_id: int) -> models.StudentProfile:
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    student_user = db.query(models.User).filter(models.User.id == student.user_id).first() if student else None
    if not student or not student_user or student_user.school_id != school_id:
        raise HTTPException(status_code=404, detail="Élève introuvable dans cet établissement")
    return student


def _ensure(current_user: models.User, roles: set) -> None:
    if current_user.role not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")


# --------------------------------------------------------------------------- #
# Guardians
# --------------------------------------------------------------------------- #
@router.get("/students/{student_id}/guardians", response_model=List[schemas.GuardianResponse])
def list_guardians(student_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _student_in_school(db, student_id, _school_id(current_user))
    return db.query(models.StudentGuardian).filter(models.StudentGuardian.student_id == student_id).order_by(models.StudentGuardian.is_primary.desc(), models.StudentGuardian.id.asc()).all()


@router.post("/students/{student_id}/guardians", response_model=schemas.GuardianResponse)
def add_guardian(student_id: int, payload: schemas.GuardianCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure(current_user, ADMIN_ROLES)
    _student_in_school(db, student_id, _school_id(current_user))
    row = models.StudentGuardian(**payload.model_dump(), student_id=student_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/guardians/{guardian_id}")
def delete_guardian(guardian_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure(current_user, ADMIN_ROLES)
    row = db.query(models.StudentGuardian).filter(models.StudentGuardian.id == guardian_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tuteur introuvable")
    _student_in_school(db, row.student_id, _school_id(current_user))
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# --------------------------------------------------------------------------- #
# Emergency contacts
# --------------------------------------------------------------------------- #
@router.get("/students/{student_id}/emergency-contacts", response_model=List[schemas.EmergencyContactResponse])
def list_emergency_contacts(student_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _student_in_school(db, student_id, _school_id(current_user))
    return db.query(models.StudentEmergencyContact).filter(models.StudentEmergencyContact.student_id == student_id).order_by(models.StudentEmergencyContact.priority.asc()).all()


@router.post("/students/{student_id}/emergency-contacts", response_model=schemas.EmergencyContactResponse)
def add_emergency_contact(student_id: int, payload: schemas.EmergencyContactCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure(current_user, ADMIN_ROLES)
    _student_in_school(db, student_id, _school_id(current_user))
    row = models.StudentEmergencyContact(**payload.model_dump(), student_id=student_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/emergency-contacts/{contact_id}")
def delete_emergency_contact(contact_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure(current_user, ADMIN_ROLES)
    row = db.query(models.StudentEmergencyContact).filter(models.StudentEmergencyContact.id == contact_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Contact introuvable")
    _student_in_school(db, row.student_id, _school_id(current_user))
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# --------------------------------------------------------------------------- #
# Medical record (one per student, restricted)
# --------------------------------------------------------------------------- #
@router.get("/students/{student_id}/medical-record", response_model=schemas.MedicalRecordResponse)
def get_medical_record(student_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure(current_user, MEDICAL_ROLES)
    _student_in_school(db, student_id, _school_id(current_user))
    row = db.query(models.StudentMedicalRecord).filter(models.StudentMedicalRecord.student_id == student_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Aucun dossier médical")
    return row


@router.put("/students/{student_id}/medical-record", response_model=schemas.MedicalRecordResponse)
def upsert_medical_record(student_id: int, payload: schemas.MedicalRecordUpsert, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure(current_user, MEDICAL_ROLES)
    _student_in_school(db, student_id, _school_id(current_user))
    row = db.query(models.StudentMedicalRecord).filter(models.StudentMedicalRecord.student_id == student_id).first()
    if not row:
        row = models.StudentMedicalRecord(student_id=student_id)
        db.add(row)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row
