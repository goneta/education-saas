from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from datetime import datetime

from .. import models, schemas, database, security

router = APIRouter(
    prefix="/finance",
    tags=["finance"]
)


def _apply_school_scope(query, model, current_user: models.User):
    if current_user.school_id:
        return query.filter(model.school_id == current_user.school_id)
    return query


def _get_fee_or_404(fee_id: int, db: Session, current_user: models.User) -> models.Fee:
    query = db.query(models.Fee).options(selectinload(models.Fee.payments)).filter(models.Fee.id == fee_id)
    query = _apply_school_scope(query, models.Fee, current_user)
    fee = query.first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee not found")
    return fee


def _recalculate_fee_status(fee: models.Fee) -> None:
    total_paid = sum(payment.amount for payment in fee.payments)
    if total_paid <= 0:
        if fee.due_date and fee.due_date < datetime.now():
            fee.status = models.FeeStatus.OVERDUE
        else:
            fee.status = models.FeeStatus.PENDING
    elif total_paid < fee.amount:
        fee.status = models.FeeStatus.PARTIAL
    else:
        fee.status = models.FeeStatus.PAID


@router.get("/fees", response_model=List[schemas.FeeResponse])
def get_fees(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Fee).options(selectinload(models.Fee.payments))
    query = _apply_school_scope(query, models.Fee, current_user)

    if status:
        query = query.filter(models.Fee.status == status)

    return query.order_by(models.Fee.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/fees", response_model=schemas.FeeResponse)
def create_fee(
    fee: schemas.FeeCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    school_id = current_user.school_id or fee.school_id

    if fee.student_id:
        student = db.query(models.StudentProfile).filter(models.StudentProfile.id == fee.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        if current_user.school_id and student.user and student.user.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Not authorized for this school")

    new_fee = models.Fee(**fee.model_dump(exclude={"school_id"}), school_id=school_id)
    db.add(new_fee)
    db.commit()
    db.refresh(new_fee)
    return new_fee


@router.put("/fees/{fee_id}", response_model=schemas.FeeResponse)
def update_fee(
    fee_id: int,
    fee_update: schemas.FeeCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_fee = _get_fee_or_404(fee_id, db, current_user)

    for field, value in fee_update.model_dump(exclude={"school_id"}).items():
        setattr(db_fee, field, value)

    if not current_user.school_id:
        db_fee.school_id = fee_update.school_id

    _recalculate_fee_status(db_fee)
    db.commit()
    db.refresh(db_fee)
    return db_fee


@router.delete("/fees/{fee_id}")
def delete_fee(
    fee_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_fee = _get_fee_or_404(fee_id, db, current_user)
    db.delete(db_fee)
    db.commit()
    return {"message": "Fee deleted successfully"}


@router.post("/fees/{fee_id}/payments", response_model=schemas.FeeResponse)
def record_fee_payment(
    fee_id: int,
    payment: schemas.PaymentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")

    db_fee = _get_fee_or_404(fee_id, db, current_user)
    db_payment = models.Payment(fee_id=db_fee.id, amount=payment.amount, note=payment.note)
    db.add(db_payment)
    db.flush()
    db.refresh(db_fee)
    _recalculate_fee_status(db_fee)
    db.commit()
    db.refresh(db_fee)
    return db_fee


@router.get("/expenses", response_model=List[schemas.ExpenseResponse])
def get_expenses(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Expense)
    query = _apply_school_scope(query, models.Expense, current_user)

    if category:
        query = query.filter(models.Expense.category == category)

    return query.order_by(models.Expense.date.desc().nullslast(), models.Expense.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/expenses", response_model=schemas.ExpenseResponse)
def create_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    school_id = current_user.school_id or expense.school_id
    new_expense = models.Expense(**expense.model_dump(exclude={"school_id"}), school_id=school_id)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


@router.put("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: schemas.ExpenseCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Expense).filter(models.Expense.id == expense_id)
    query = _apply_school_scope(query, models.Expense, current_user)
    db_expense = query.first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    for field, value in expense_update.model_dump(exclude={"school_id"}).items():
        setattr(db_expense, field, value)

    if not current_user.school_id:
        db_expense.school_id = expense_update.school_id

    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Expense).filter(models.Expense.id == expense_id)
    query = _apply_school_scope(query, models.Expense, current_user)
    db_expense = query.first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(db_expense)
    db.commit()
    return {"message": "Expense deleted successfully"}
