from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from datetime import datetime, time
from uuid import uuid4

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


def _school_id_for(current_user: models.User, explicit_school_id: Optional[int] = None) -> int:
    school_id = current_user.school_id or explicit_school_id
    if not school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return school_id


def _payments_query(db: Session, current_user: models.User):
    query = db.query(models.Payment).join(models.Fee)
    if current_user.school_id:
        query = query.filter(models.Fee.school_id == current_user.school_id)
    return query


def _parse_date(value: Optional[str], end_of_day: bool = False):
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.time() == time.min and end_of_day:
        return datetime.combine(parsed.date(), time.max)
    return parsed


def _serialize_payment(payment: models.Payment):
    fee = payment.fee
    student = fee.student if fee else None
    user = student.user if student and student.user else None
    class_ = student.current_class if student and student.current_class else None
    return {
        "id": payment.id,
        "amount": payment.amount,
        "payment_date": payment.payment_date,
        "receipt_number": payment.receipt_number,
        "note": payment.note,
        "operator_station": payment.operator_station,
        "recorded_by_id": payment.recorded_by_id,
        "recorded_by": payment.recorded_by.full_name if payment.recorded_by else None,
        "fee_id": fee.id if fee else None,
        "fee_title": fee.title if fee else None,
        "fee_category": fee.category if fee else None,
        "student_id": student.id if student else None,
        "student_user_id": user.id if user else None,
        "student_name": user.full_name if user else None,
        "registration_number": student.registration_number if student else None,
        "class_id": class_.id if class_ else None,
        "class_name": class_.name if class_ else None,
    }


def _serialize_fee(fee: models.Fee):
    payments = list(fee.payments or [])
    total_paid = sum(payment.amount for payment in payments)
    return {
        "id": fee.id,
        "title": fee.title,
        "amount": fee.amount,
        "due_date": fee.due_date,
        "status": fee.status,
        "description": fee.description,
        "category": fee.category,
        "category_order": fee.category_order or 0,
        "is_required": bool(fee.is_required),
        "academic_year_id": fee.academic_year_id,
        "class_id": fee.class_id,
        "covered_by": fee.covered_by,
        "student_id": fee.student_id,
        "school_id": fee.school_id,
        "created_at": fee.created_at,
        "payments": payments,
        "total_paid": total_paid,
        "remaining_balance": max(fee.amount - total_paid, 0),
    }


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
    student_id: Optional[int] = None,
    class_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Fee).options(selectinload(models.Fee.payments))
    query = _apply_school_scope(query, models.Fee, current_user)

    if status:
        query = query.filter(models.Fee.status == status)
    if student_id:
        query = query.outerjoin(models.StudentProfile).filter(
            (models.Fee.student_id == student_id) |
            (models.StudentProfile.user_id == student_id)
        )
    if class_id:
        query = query.filter(models.Fee.class_id == class_id)
    if category:
        query = query.filter(models.Fee.category == category)

    return [_serialize_fee(fee) for fee in query.order_by(models.Fee.created_at.desc()).offset(skip).limit(limit).all()]


@router.post("/fees", response_model=schemas.FeeResponse)
def create_fee(
    fee: schemas.FeeCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    school_id = current_user.school_id or fee.school_id

    if fee.student_id:
        student = db.query(models.StudentProfile).filter(
            (models.StudentProfile.id == fee.student_id) |
            (models.StudentProfile.user_id == fee.student_id)
        ).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        if current_user.school_id and student.user and student.user.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Not authorized for this school")
        fee.student_id = student.id

    fee_data = fee.model_dump(exclude={"school_id"})
    fee_data["due_date"] = fee_data["due_date"] or datetime.utcnow()
    new_fee = models.Fee(**fee_data, school_id=school_id)
    db.add(new_fee)
    db.commit()
    db.refresh(new_fee)
    return _serialize_fee(new_fee)


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
    return _serialize_fee(db_fee)


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
    paid_before = sum(existing.amount for existing in db_fee.payments)
    if payment.amount > max(db_fee.amount - paid_before, 0):
        raise HTTPException(status_code=400, detail="Payment amount exceeds remaining balance")
    db_payment = models.Payment(
        fee_id=db_fee.id,
        amount=payment.amount,
        payment_date=payment.payment_date or datetime.utcnow(),
        note=payment.note,
        operator_station=payment.operator_station,
        recorded_by_id=current_user.id,
        receipt_number=f"RCPT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}",
    )
    db_fee.payments.append(db_payment)
    db.flush()
    _recalculate_fee_status(db_fee)
    db.commit()
    return _serialize_fee(_get_fee_or_404(fee_id, db, current_user))


@router.get("/payments")
def list_payments(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    operator_id: Optional[int] = None,
    class_id: Optional[int] = None,
    fee_category: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = _payments_query(db, current_user).options(
        selectinload(models.Payment.recorded_by),
        selectinload(models.Payment.fee).selectinload(models.Fee.student).selectinload(models.StudentProfile.user),
        selectinload(models.Payment.fee).selectinload(models.Fee.student).selectinload(models.StudentProfile.current_class),
    )
    start = _parse_date(start_date)
    end = _parse_date(end_date, end_of_day=True)
    if start:
        query = query.filter(models.Payment.payment_date >= start)
    if end:
        query = query.filter(models.Payment.payment_date <= end)
    if operator_id:
        query = query.filter(models.Payment.recorded_by_id == operator_id)
    if fee_category:
        query = query.filter(models.Fee.category == fee_category)
    if class_id:
        query = query.outerjoin(models.StudentProfile, models.Fee.student_id == models.StudentProfile.id).filter(
            (models.Fee.class_id == class_id) |
            (models.StudentProfile.current_class_id == class_id)
        )
    return [_serialize_payment(payment) for payment in query.order_by(models.Payment.payment_date.desc()).all()]


@router.get("/cash-journal")
def cash_journal(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    operator_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    payments = list_payments(start_date, end_date, operator_id, None, None, db, current_user)
    by_category = {}
    by_operator = {}
    for payment in payments:
        category = payment["fee_category"] or payment["fee_title"] or "Autres"
        by_category[category] = by_category.get(category, 0) + payment["amount"]
        operator = payment["recorded_by"] or "Non renseigné"
        by_operator[operator] = by_operator.get(operator, 0) + payment["amount"]
    return {
        "payments": payments,
        "total": sum(payment["amount"] for payment in payments),
        "by_category": by_category,
        "by_operator": by_operator,
    }


@router.post("/cash-closures", response_model=schemas.CashClosureResponse)
def create_cash_closure(
    closure: schemas.CashClosureCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    school_id = _school_id_for(current_user)
    day_start = datetime.combine(closure.closure_date.date(), time.min)
    day_end = datetime.combine(closure.closure_date.date(), time.max)
    expected = _payments_query(db, current_user).filter(
        models.Payment.payment_date >= day_start,
        models.Payment.payment_date <= day_end,
    ).with_entities(func.coalesce(func.sum(models.Payment.amount), 0)).scalar()
    row = models.CashClosure(
        closure_date=closure.closure_date,
        counted_amount=closure.counted_amount,
        expected_amount=expected,
        difference=closure.counted_amount - expected,
        notes=closure.notes,
        school_id=school_id,
        submitted_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/cash-closures/{closure_id}/approve", response_model=schemas.CashClosureResponse)
def approve_cash_closure(
    closure_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN, models.UserRole.DIRECTION]:
        raise HTTPException(status_code=403, detail="Manager validation required")
    query = db.query(models.CashClosure).filter(models.CashClosure.id == closure_id)
    query = _apply_school_scope(query, models.CashClosure, current_user)
    closure = query.first()
    if not closure:
        raise HTTPException(status_code=404, detail="Cash closure not found")
    closure.status = models.CashClosureStatus.APPROVED
    closure.approved_by_id = current_user.id
    closure.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(closure)
    return closure


@router.get("/reports")
def finance_reports(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    class_id: Optional[int] = None,
    fee_category: Optional[str] = None,
    operator_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    payments = list_payments(start_date, end_date, operator_id, class_id, fee_category, db, current_user)
    fee_query = db.query(models.Fee).options(
        selectinload(models.Fee.payments),
        selectinload(models.Fee.student).selectinload(models.StudentProfile.user),
        selectinload(models.Fee.student).selectinload(models.StudentProfile.current_class),
        selectinload(models.Fee.class_),
    )
    fee_query = _apply_school_scope(fee_query, models.Fee, current_user)
    if fee_category:
        fee_query = fee_query.filter(models.Fee.category == fee_category)
    if class_id:
        fee_query = fee_query.outerjoin(models.StudentProfile, models.Fee.student_id == models.StudentProfile.id).filter(
            (models.Fee.class_id == class_id) |
            (models.StudentProfile.current_class_id == class_id)
        )
    fees = fee_query.all()
    debtors = []
    by_class = {}
    by_category = {}
    for fee in fees:
        student = fee.student
        class_name = fee.class_.name if fee.class_ else student.current_class.name if student and student.current_class else "Sans classe"
        remaining = fee.remaining_balance
        if remaining > 0 and student:
            debtors.append({
                "student_id": student.id,
                "student_user_id": student.user_id,
                "student_name": student.user.full_name if student.user else None,
                "registration_number": student.registration_number,
                "class_name": class_name,
                "fee_title": fee.title,
                "amount": fee.amount,
                "paid": fee.total_paid,
                "remaining": remaining,
            })
        by_class[class_name] = by_class.get(class_name, 0) + fee.total_paid
        category = fee.category or fee.title
        by_category[category] = by_category.get(category, 0) + fee.total_paid
    return {
        "total_expected": sum(fee.amount for fee in fees),
        "total_paid": sum(payment["amount"] for payment in payments),
        "total_remaining": sum(fee.remaining_balance for fee in fees),
        "payments_by_class": by_class,
        "payments_by_category": by_category,
        "debtors": debtors,
        "student_details": debtors,
        "payments": payments,
    }


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


@router.get("/fee-schedules", response_model=List[schemas.FeeScheduleResponse])
def list_fee_schedules(
    academic_year_id: Optional[int] = None,
    class_id: Optional[int] = None,
    level: Optional[str] = None,
    current_only: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.FeeSchedule)
    query = _apply_school_scope(query, models.FeeSchedule, current_user)
    if academic_year_id:
        query = query.filter(models.FeeSchedule.academic_year_id == academic_year_id)
    if class_id:
        query = query.filter(models.FeeSchedule.class_id == class_id)
    if level:
        query = query.filter(models.FeeSchedule.level == level)
    if current_only:
        query = query.filter(models.FeeSchedule.is_current == True)
    return query.order_by(models.FeeSchedule.category_order.asc(), models.FeeSchedule.name.asc()).all()


@router.post("/fee-schedules", response_model=schemas.FeeScheduleResponse)
def create_fee_schedule(
    schedule: schemas.FeeScheduleCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    school_id = _school_id_for(current_user, schedule.school_id)
    row = models.FeeSchedule(**schedule.model_dump(exclude={"school_id"}), school_id=school_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/fee-schedules/copy-year")
def copy_fee_schedules_to_year(
    source_academic_year_id: int,
    target_academic_year_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    school_id = _school_id_for(current_user)
    source_rows = db.query(models.FeeSchedule).filter(
        models.FeeSchedule.school_id == school_id,
        models.FeeSchedule.academic_year_id == source_academic_year_id,
    ).all()
    created = 0
    for row in source_rows:
        exists = db.query(models.FeeSchedule).filter(
            models.FeeSchedule.school_id == school_id,
            models.FeeSchedule.academic_year_id == target_academic_year_id,
            models.FeeSchedule.name == row.name,
            models.FeeSchedule.class_id == row.class_id,
            models.FeeSchedule.level == row.level,
        ).first()
        if exists:
            continue
        db.add(models.FeeSchedule(
            name=row.name,
            amount=row.amount,
            category_order=row.category_order,
            is_required=row.is_required,
            is_current=True,
            academic_year_id=target_academic_year_id,
            class_id=row.class_id,
            level=row.level,
            school_id=school_id,
        ))
        created += 1
    db.commit()
    return {"created": created, "message": "Fee schedules copied from previous year"}


@router.get("/forecasts", response_model=List[schemas.BudgetForecastResponse])
def list_forecasts(
    academic_year_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.BudgetForecast)
    query = _apply_school_scope(query, models.BudgetForecast, current_user)
    if academic_year_id:
        query = query.filter(models.BudgetForecast.academic_year_id == academic_year_id)
    return query.order_by(models.BudgetForecast.created_at.desc()).all()


@router.post("/forecasts", response_model=schemas.BudgetForecastResponse)
def create_forecast(
    forecast: schemas.BudgetForecastCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    school_id = _school_id_for(current_user, forecast.school_id)
    row = models.BudgetForecast(
        **forecast.model_dump(exclude={"school_id"}),
        school_id=school_id,
        created_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/forecast-vs-actual")
def forecast_vs_actual(
    academic_year_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    forecasts = list_forecasts(academic_year_id, db, current_user)
    actual_query = db.query(models.Fee).options(selectinload(models.Fee.payments))
    actual_query = _apply_school_scope(actual_query, models.Fee, current_user)
    actual = actual_query.all()
    total_expected = sum(row.expected_revenue for row in forecasts)
    total_actual = sum(fee.total_paid for fee in actual if not academic_year_id or fee.academic_year_id == academic_year_id)
    return {
        "expected_revenue": total_expected,
        "actual_revenue": total_actual,
        "difference": total_actual - total_expected,
        "forecast_rows": forecasts,
    }


@router.post("/sms", response_model=schemas.SmsMessageResponse)
def queue_sms(
    message: schemas.SmsMessageCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    school_id = _school_id_for(current_user)
    row = models.SmsMessage(
        **message.model_dump(),
        school_id=school_id,
        created_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
