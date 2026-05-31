from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(prefix="/operations", tags=["Institution Operations"])

OPERATIONS_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.REGISTRAR,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _ensure_manager(current_user: models.User) -> None:
    if current_user.role not in OPERATIONS_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")


def _inventory_status(quantity: int, minimum_quantity: int) -> models.InventoryStatus:
    if quantity <= 0:
        return models.InventoryStatus.OUT_OF_STOCK
    if quantity <= minimum_quantity:
        return models.InventoryStatus.LOW_STOCK
    return models.InventoryStatus.AVAILABLE


@router.get("/programs", response_model=List[schemas.AcademicProgramResponse])
def list_programs(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.AcademicProgram).filter(models.AcademicProgram.school_id == _school_id(current_user)).order_by(models.AcademicProgram.name.asc()).all()


@router.post("/programs", response_model=schemas.AcademicProgramResponse)
def create_program(program: schemas.AcademicProgramCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = models.AcademicProgram(**program.model_dump(), school_id=_school_id(current_user))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/admissions", response_model=List[schemas.AdmissionApplicationResponse])
def list_admissions(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    return db.query(models.AdmissionApplication).filter(models.AdmissionApplication.school_id == _school_id(current_user)).order_by(models.AdmissionApplication.created_at.desc()).all()


@router.post("/admissions", response_model=schemas.AdmissionApplicationResponse)
def create_admission(application: schemas.AdmissionApplicationCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = models.AdmissionApplication(**application.model_dump(), school_id=_school_id(current_user), handled_by_id=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/admissions/{application_id}", response_model=schemas.AdmissionApplicationResponse)
def update_admission(application_id: int, update: schemas.AdmissionApplicationUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = db.query(models.AdmissionApplication).filter(models.AdmissionApplication.id == application_id, models.AdmissionApplication.school_id == _school_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Admission application not found")
    row.status = update.status
    row.notes = update.notes
    row.handled_by_id = current_user.id
    db.commit()
    db.refresh(row)
    return row


@router.get("/exams", response_model=List[schemas.ExamSessionResponse])
def list_exam_sessions(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.ExamSession).filter(models.ExamSession.school_id == _school_id(current_user)).order_by(models.ExamSession.created_at.desc()).all()


@router.post("/exams", response_model=schemas.ExamSessionResponse)
def create_exam_session(exam: schemas.ExamSessionCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = models.ExamSession(**exam.model_dump(), school_id=_school_id(current_user), created_by_id=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/inventory", response_model=List[schemas.InventoryItemResponse])
def list_inventory(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    return db.query(models.InventoryItem).filter(models.InventoryItem.school_id == _school_id(current_user)).order_by(models.InventoryItem.category.asc(), models.InventoryItem.name.asc()).all()


@router.post("/inventory", response_model=schemas.InventoryItemResponse)
def create_inventory_item(item: schemas.InventoryItemCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = models.InventoryItem(
        **item.model_dump(),
        status=_inventory_status(item.quantity, item.minimum_quantity),
        school_id=_school_id(current_user),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/payroll", response_model=List[schemas.PayrollRecordResponse])
def list_payroll(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    return db.query(models.PayrollRecord).filter(models.PayrollRecord.school_id == _school_id(current_user)).order_by(models.PayrollRecord.created_at.desc()).all()


@router.post("/payroll", response_model=schemas.PayrollRecordResponse)
def create_payroll(record: schemas.PayrollRecordCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    staff = db.query(models.User).filter(models.User.id == record.staff_user_id, models.User.school_id == _school_id(current_user)).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff user not found")
    row = models.PayrollRecord(
        **record.model_dump(),
        net_amount=record.gross_amount - record.deductions,
        school_id=_school_id(current_user),
        created_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/payroll/{record_id}", response_model=schemas.PayrollRecordResponse)
def update_payroll(record_id: int, update: schemas.PayrollRecordUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = db.query(models.PayrollRecord).filter(models.PayrollRecord.id == record_id, models.PayrollRecord.school_id == _school_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    row.status = update.status
    row.paid_at = datetime.utcnow() if update.status == models.PayrollStatus.PAID else row.paid_at
    db.commit()
    db.refresh(row)
    return row


@router.get("/transport", response_model=List[schemas.TransportRouteResponse])
def list_transport(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.TransportRoute).filter(models.TransportRoute.school_id == _school_id(current_user)).order_by(models.TransportRoute.name.asc()).all()


@router.post("/transport", response_model=schemas.TransportRouteResponse)
def create_transport(route: schemas.TransportRouteCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = models.TransportRoute(**route.model_dump(), school_id=_school_id(current_user))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/canteen", response_model=List[schemas.CanteenMealPlanResponse])
def list_canteen(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.CanteenMealPlan).filter(models.CanteenMealPlan.school_id == _school_id(current_user)).order_by(models.CanteenMealPlan.day_of_week.asc().nullslast(), models.CanteenMealPlan.name.asc()).all()


@router.post("/canteen", response_model=schemas.CanteenMealPlanResponse)
def create_canteen_plan(plan: schemas.CanteenMealPlanCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = models.CanteenMealPlan(**plan.model_dump(), school_id=_school_id(current_user))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
