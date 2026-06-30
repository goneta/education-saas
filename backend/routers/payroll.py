"""Payroll / Paie (#7) — a real payroll system under Finance.

Per-employee salary profiles feed a country-extensible calculation engine
(`services/payroll.py`) that produces full gross → net payslips with itemised
lines (allowances, bonuses, overtime, deductions, advances). Admins/accountants
manage and pay; employees and teachers see only their own payslips
(self-service). Payment is method-agnostic (bank transfer, cash, Stripe,
CinetPay, Djamo) — the actual gateway call is handled by the Payment Service.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import audit, database, models, schemas, security
from ..services import payroll as payroll_engine

router = APIRouter(prefix="/finance/payroll", tags=["Payroll"])

_ADMIN_ROLES = (models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN, models.UserRole.ACCOUNTANT)


def _ensure_admin(current_user: models.User) -> None:
    if current_user.role not in _ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Réservé à l'administration / comptabilité.")


def _school_id(current_user: models.User, school_id: Optional[int]) -> int:
    if current_user.role == models.UserRole.SUPER_ADMIN:
        if not school_id:
            raise HTTPException(status_code=400, detail="school_id requis pour le Super Admin.")
        return school_id
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Contexte d'établissement requis.")
    return current_user.school_id


# --- Salary profiles ---------------------------------------------------------

def _profile_response(profile: models.SalaryProfile, user: Optional[models.User]) -> schemas.SalaryProfileResponse:
    return schemas.SalaryProfileResponse(
        id=profile.id, user_id=profile.user_id, school_id=profile.school_id,
        employee_type=profile.employee_type, pay_type=profile.pay_type, base_rate=profile.base_rate,
        currency=profile.currency, country_code=profile.country_code, cotisation_rate=profile.cotisation_rate,
        tax_rate=profile.tax_rate, is_active=profile.is_active,
        full_name=user.full_name if user else None, email=user.email if user else None,
    )


@router.get("/salary-profiles", response_model=List[schemas.SalaryProfileResponse])
def list_salary_profiles(school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    rows = (
        db.query(models.SalaryProfile, models.User)
        .join(models.User, models.User.id == models.SalaryProfile.user_id)
        .filter(models.SalaryProfile.school_id == resolved)
        .order_by(models.User.full_name.asc())
        .all()
    )
    return [_profile_response(p, u) for p, u in rows]


@router.post("/salary-profiles", response_model=schemas.SalaryProfileResponse, status_code=201)
def create_salary_profile(payload: schemas.SalaryProfileCreate, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    if payload.employee_type not in schemas.EMPLOYEE_TYPES:
        raise HTTPException(status_code=422, detail=f"Type d'employé invalide : {payload.employee_type}")
    if payload.pay_type not in schemas.PAY_TYPES:
        raise HTTPException(status_code=422, detail=f"Type de paie invalide : {payload.pay_type}")
    user = db.query(models.User).filter(models.User.id == payload.user_id, models.User.school_id == resolved).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employé introuvable dans cet établissement.")
    if db.query(models.SalaryProfile.id).filter(models.SalaryProfile.user_id == payload.user_id).first():
        raise HTTPException(status_code=409, detail="Un profil de salaire existe déjà pour cet employé.")
    profile = models.SalaryProfile(school_id=resolved, **payload.model_dump())
    db.add(profile)
    audit.record_audit(db, action="payroll.salary_profile.created", current_user=current_user, entity_type="salary_profile", entity_id=payload.user_id)
    db.commit()
    db.refresh(profile)
    return _profile_response(profile, user)


@router.patch("/salary-profiles/{profile_id}", response_model=schemas.SalaryProfileResponse)
def update_salary_profile(profile_id: int, payload: schemas.SalaryProfileUpdate, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    profile = db.query(models.SalaryProfile).filter(models.SalaryProfile.id == profile_id, models.SalaryProfile.school_id == resolved).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil de salaire introuvable.")
    data = payload.model_dump(exclude_unset=True)
    if data.get("employee_type") and data["employee_type"] not in schemas.EMPLOYEE_TYPES:
        raise HTTPException(status_code=422, detail=f"Type d'employé invalide : {data['employee_type']}")
    if data.get("pay_type") and data["pay_type"] not in schemas.PAY_TYPES:
        raise HTTPException(status_code=422, detail=f"Type de paie invalide : {data['pay_type']}")
    for key, value in data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    user = db.query(models.User).filter(models.User.id == profile.user_id).first()
    return _profile_response(profile, user)


# --- Payslips ----------------------------------------------------------------

def _serialize_payslip(db: Session, record: models.PayrollRecord, user: Optional[models.User] = None) -> schemas.PayslipResponse:
    if user is None:
        user = db.query(models.User).filter(models.User.id == record.staff_user_id).first()
    lines = db.query(models.PayrollAdjustment).filter(models.PayrollAdjustment.payroll_record_id == record.id).all()
    return schemas.PayslipResponse(
        id=record.id, staff_user_id=record.staff_user_id,
        full_name=user.full_name if user else None, email=user.email if user else None,
        school_id=record.school_id, period=record.period, period_type=record.period_type, pay_type=record.pay_type,
        currency=record.currency, base_amount=record.base_amount, allowances_total=record.allowances_total,
        bonus_total=record.bonus_total, overtime_total=record.overtime_total, advances_total=record.advances_total,
        other_deductions_total=record.other_deductions_total, gross_amount=record.gross_amount,
        social_contributions=record.social_contributions, tax_amount=record.tax_amount, deductions=record.deductions,
        net_amount=record.net_amount, status=record.status, payment_method=record.payment_method,
        payment_reference=record.payment_reference, paid_at=record.paid_at, created_at=record.created_at,
        lines=[schemas.PayslipLine(type=a.adjustment_type, label=a.label, amount=a.amount, is_taxable=a.is_taxable) for a in lines],
    )


@router.post("/payslips/generate", response_model=schemas.PayslipResponse, status_code=201)
def generate_payslip(payload: schemas.PayslipGenerate, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    if payload.period_type not in ("weekly", "monthly"):
        raise HTTPException(status_code=422, detail=f"Période invalide : {payload.period_type}")
    profile = db.query(models.SalaryProfile).filter(models.SalaryProfile.user_id == payload.staff_user_id, models.SalaryProfile.school_id == resolved).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Aucun profil de salaire pour cet employé. Configurez-le d'abord.")
    if db.query(models.PayrollRecord.id).filter(
        models.PayrollRecord.staff_user_id == payload.staff_user_id,
        models.PayrollRecord.school_id == resolved,
        models.PayrollRecord.period == payload.period,
        models.PayrollRecord.period_type == payload.period_type,
    ).first():
        raise HTTPException(status_code=409, detail=f"Un bulletin existe déjà pour cette période ({payload.period}).")

    base = payload.base_amount_override if payload.base_amount_override is not None else payroll_engine.base_amount_for(profile.pay_type, profile.base_rate, payload.units)
    lines = [payroll_engine.PayslipLine(type=l.type, label=l.label, amount=l.amount, is_taxable=l.is_taxable) for l in payload.lines]
    comp = payroll_engine.compute(base, lines, profile.cotisation_rate, profile.tax_rate, profile.country_code)

    record = models.PayrollRecord(
        staff_user_id=payload.staff_user_id, period=payload.period, gross_amount=comp.gross_amount,
        deductions=comp.total_deductions, net_amount=comp.net_amount, status=models.PayrollStatus.DRAFT,
        school_id=resolved, created_by_id=current_user.id, period_type=payload.period_type, pay_type=profile.pay_type,
        currency=profile.currency, country_code=profile.country_code, base_amount=comp.base_amount,
        allowances_total=comp.allowances_total, bonus_total=comp.bonus_total, overtime_total=comp.overtime_total,
        advances_total=comp.advances_total, other_deductions_total=comp.other_deductions_total,
        social_contributions=comp.social_contributions, tax_amount=comp.tax_amount, academic_year_id=payload.academic_year_id,
    )
    db.add(record)
    db.flush()
    for line in payload.lines:
        db.add(models.PayrollAdjustment(payroll_record_id=record.id, adjustment_type=line.type, label=line.label, amount=line.amount, is_taxable=line.is_taxable))
    audit.record_audit(db, action="payroll.payslip.generated", current_user=current_user, entity_type="payroll_record", entity_id=record.id)
    db.commit()
    db.refresh(record)
    return _serialize_payslip(db, record)


@router.get("/payslips", response_model=List[schemas.PayslipResponse])
def list_payslips(staff_user_id: Optional[int] = None, period: Optional[str] = None, status: Optional[models.PayrollStatus] = None, period_type: Optional[str] = None, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    query = db.query(models.PayrollRecord).filter(models.PayrollRecord.school_id == resolved)
    if staff_user_id:
        query = query.filter(models.PayrollRecord.staff_user_id == staff_user_id)
    if period:
        query = query.filter(models.PayrollRecord.period == period)
    if status:
        query = query.filter(models.PayrollRecord.status == status)
    if period_type:
        query = query.filter(models.PayrollRecord.period_type == period_type)
    records = query.order_by(models.PayrollRecord.created_at.desc()).all()
    return [_serialize_payslip(db, record) for record in records]


@router.get("/payslips/me", response_model=List[schemas.PayslipResponse])
def my_payslips(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Self-service — an employee/teacher sees only their own payslips."""
    records = (
        db.query(models.PayrollRecord)
        .filter(models.PayrollRecord.staff_user_id == current_user.id)
        .order_by(models.PayrollRecord.created_at.desc())
        .all()
    )
    return [_serialize_payslip(db, record, current_user) for record in records]


@router.get("/payslips/{record_id}", response_model=schemas.PayslipResponse)
def get_payslip(record_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    record = db.query(models.PayrollRecord).filter(models.PayrollRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Bulletin introuvable.")
    is_owner = record.staff_user_id == current_user.id
    is_admin = current_user.role in _ADMIN_ROLES and (current_user.role == models.UserRole.SUPER_ADMIN or record.school_id == current_user.school_id)
    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Accès refusé.")
    return _serialize_payslip(db, record)


@router.post("/payslips/{record_id}/approve", response_model=schemas.PayslipResponse)
def approve_payslip(record_id: int, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    record = db.query(models.PayrollRecord).filter(models.PayrollRecord.id == record_id, models.PayrollRecord.school_id == resolved).first()
    if not record:
        raise HTTPException(status_code=404, detail="Bulletin introuvable.")
    record.status = models.PayrollStatus.APPROVED
    audit.record_audit(db, action="payroll.payslip.approved", current_user=current_user, entity_type="payroll_record", entity_id=record.id)
    db.commit()
    db.refresh(record)
    return _serialize_payslip(db, record)


@router.post("/payslips/{record_id}/pay", response_model=schemas.PayslipResponse)
def pay_payslip(record_id: int, payload: schemas.PayslipPay, school_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_admin(current_user)
    resolved = _school_id(current_user, school_id)
    if payload.payment_method not in schemas.PAYROLL_PAYMENT_METHODS:
        raise HTTPException(status_code=422, detail=f"Méthode de paiement invalide : {payload.payment_method}")
    record = db.query(models.PayrollRecord).filter(models.PayrollRecord.id == record_id, models.PayrollRecord.school_id == resolved).first()
    if not record:
        raise HTTPException(status_code=404, detail="Bulletin introuvable.")
    record.status = models.PayrollStatus.PAID
    record.payment_method = payload.payment_method
    record.payment_reference = payload.payment_reference
    record.paid_at = datetime.utcnow()
    audit.record_audit(db, action="payroll.payslip.paid", current_user=current_user, entity_type="payroll_record", entity_id=record.id, details={"method": payload.payment_method})
    db.commit()
    db.refresh(record)
    return _serialize_payslip(db, record)
