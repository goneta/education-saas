from datetime import datetime
from typing import List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from .. import crypto_utils, database, models, rbac, schemas, security
from ..services.notification_service import dispatch_notification

router = APIRouter(prefix="/enterprise", tags=["Enterprise"])

MANAGER_ROLES = {models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION, models.UserRole.REGISTRAR}
APPROVAL_LOCKED_RESOURCES = {"vendor-invoices", "leaves", "contracts", "diplomas", "transcripts", "bank-transactions"}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _manager(current_user: models.User):
    if current_user.role not in MANAGER_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")


def _list(db: Session, model: Type, current_user: models.User):
    return db.query(model).filter(model.school_id == _school_id(current_user)).all()


def _create(db: Session, model: Type, payload, current_user: models.User, extra=None):
    _manager(current_user)
    row = model(**payload.model_dump(), school_id=_school_id(current_user), **(extra or {}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


RESOURCE_MODELS = {
    "semesters": models.Semester,
    "course-units": models.CourseUnit,
    "university-schedule": models.UniversityScheduleSlot,
    "diplomas": models.DiplomaRecord,
    "transcripts": models.CertifiedTranscript,
    "contracts": models.StaffContract,
    "leaves": models.LeaveRequest,
    "transport-assignments": models.TransportAssignment,
    "canteen-subscriptions": models.CanteenSubscription,
    "accounts": models.ChartAccount,
    "vendor-invoices": models.VendorInvoice,
    "bank-transactions": models.BankTransaction,
    "notification-providers": models.NotificationProvider,
    "course-enrollments": models.CourseEnrollment,
    "journal-entries": models.JournalEntry,
    "bank-reconciliations": models.BankReconciliation,
}


def _enterprise_read(current_user: models.User, db: Session):
    rbac.require_permission(current_user, "enterprise:read", db)


def _enterprise_write(current_user: models.User, db: Session):
    rbac.require_permission(current_user, "enterprise:write", db)
    _manager(current_user)


def _enterprise_approve(current_user: models.User, db: Session):
    rbac.require_permission(current_user, "enterprise:approve", db)
    _manager(current_user)


def _ensure_mutation_allowed(resource: str, row) -> None:
    status = getattr(row, "status", None)
    if resource in APPROVAL_LOCKED_RESOURCES and status in {
        models.ApprovalStatus.APPROVED,
        models.InvoiceStatus.APPROVED,
        models.InvoiceStatus.PAID,
        models.LeaveStatus.APPROVED,
        "approved",
        "paid",
        "certified",
    }:
        raise HTTPException(status_code=409, detail="Approved or finalized records cannot be modified directly")


def _ensure_school_row(db: Session, model: Type, row_id: Optional[int], school_id: int, label: str):
    if row_id is None:
        return None
    row = db.query(model).filter(model.id == row_id, model.school_id == school_id).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return row


@router.put("/{resource}/{row_id}")
def update_enterprise_resource(resource: str, row_id: int, payload: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_write(current_user, db)
    model = RESOURCE_MODELS.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="Resource not found")
    row = db.query(model).filter(model.id == row_id, model.school_id == _school_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    _ensure_mutation_allowed(resource, row)
    for key, value in payload.items():
        if key not in {"id", "school_id", "created_at"} and hasattr(row, key):
            if resource == "notification-providers" and key == "api_key_secret":
                value = crypto_utils.encrypt_secret(value)
            setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{resource}/{row_id}")
def delete_enterprise_resource(resource: str, row_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_write(current_user, db)
    model = RESOURCE_MODELS.get(resource)
    if not model:
        raise HTTPException(status_code=404, detail="Resource not found")
    row = db.query(model).filter(model.id == row_id, model.school_id == _school_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    _ensure_mutation_allowed(resource, row)
    db.delete(row)
    db.commit()
    return {"message": "Record deleted"}


@router.get("/approvals", response_model=List[schemas.ApprovalWorkflowResponse])
def list_approvals(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_read(current_user, db)
    return db.query(models.ApprovalWorkflow).filter(models.ApprovalWorkflow.school_id == _school_id(current_user)).order_by(models.ApprovalWorkflow.created_at.desc()).all()


@router.post("/approvals", response_model=schemas.ApprovalWorkflowResponse)
def create_approval(workflow: schemas.ApprovalWorkflowCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_write(current_user, db)
    row = models.ApprovalWorkflow(entity_type=workflow.entity_type, entity_id=workflow.entity_id, title=workflow.title, school_id=_school_id(current_user), requested_by_id=current_user.id)
    db.add(row)
    db.flush()
    for step in workflow.steps:
        db.add(models.ApprovalStep(workflow_id=row.id, step_order=step.step_order, role=step.role))
    db.commit()
    db.refresh(row)
    return row


@router.post("/approvals/{workflow_id}/decide", response_model=schemas.ApprovalWorkflowResponse)
def decide_approval(workflow_id: int, decision: schemas.ApprovalDecision, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_approve(current_user, db)
    workflow = db.query(models.ApprovalWorkflow).filter(models.ApprovalWorkflow.id == workflow_id, models.ApprovalWorkflow.school_id == _school_id(current_user)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.status != models.ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail="Workflow is already finalized")
    step = db.query(models.ApprovalStep).filter(models.ApprovalStep.workflow_id == workflow.id, models.ApprovalStep.step_order == workflow.current_step).first()
    if not step or step.role != current_user.role:
        raise HTTPException(status_code=403, detail="Current step is assigned to another role")
    if step.approver_id and step.approver_id != current_user.id:
        raise HTTPException(status_code=403, detail="This approval step is assigned to another user")
    if step.status != models.ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail="Approval step is already decided")
    step.status = decision.status
    step.comment = decision.comment
    step.approver_id = current_user.id
    step.decided_at = datetime.utcnow()
    if decision.status == models.ApprovalStatus.REJECTED:
        workflow.status = models.ApprovalStatus.REJECTED
        workflow.decided_at = datetime.utcnow()
    elif decision.status == models.ApprovalStatus.APPROVED:
        next_step = db.query(models.ApprovalStep).filter(models.ApprovalStep.workflow_id == workflow.id, models.ApprovalStep.step_order == workflow.current_step + 1).first()
        if next_step:
            workflow.current_step += 1
        else:
            workflow.status = models.ApprovalStatus.APPROVED
            workflow.decided_at = datetime.utcnow()
    db.commit()
    db.refresh(workflow)
    return workflow


@router.get("/semesters", response_model=List[schemas.SemesterResponse])
def list_semesters(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.Semester, current_user)
@router.post("/semesters", response_model=schemas.SemesterResponse)
def create_semester(payload: schemas.SemesterCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.Semester, payload, current_user)

@router.get("/course-units", response_model=List[schemas.CourseUnitResponse])
def list_course_units(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.CourseUnit, current_user)
@router.post("/course-units", response_model=schemas.CourseUnitResponse)
def create_course_unit(payload: schemas.CourseUnitCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.CourseUnit, payload, current_user)

@router.get("/course-enrollments", response_model=List[schemas.CourseEnrollmentResponse])
def list_course_enrollments(student_id: Optional[int] = None, semester_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_read(current_user, db)
    query = db.query(models.CourseEnrollment).filter(models.CourseEnrollment.school_id == _school_id(current_user))
    if student_id:
        query = query.filter(models.CourseEnrollment.student_id == student_id)
    if semester_id:
        query = query.filter(models.CourseEnrollment.semester_id == semester_id)
    return query.order_by(models.CourseEnrollment.registered_at.desc()).all()

@router.post("/course-enrollments", response_model=schemas.CourseEnrollmentResponse)
def create_course_enrollment(payload: schemas.CourseEnrollmentCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_write(current_user, db)
    school_id = _school_id(current_user)
    student = db.query(models.StudentProfile).join(models.User).filter(models.StudentProfile.id == payload.student_id, models.User.school_id == school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    course = _ensure_school_row(db, models.CourseUnit, payload.course_unit_id, school_id, "Course unit")
    if payload.semester_id:
        _ensure_school_row(db, models.Semester, payload.semester_id, school_id, "Semester")
    credits_attempted = payload.credits_attempted if payload.credits_attempted is not None else course.credits
    score = payload.score
    grade_point = payload.grade_point
    if grade_point is None and score is not None:
        grade_point = 4 if score >= 16 else 3 if score >= 14 else 2 if score >= 12 else 1 if score >= 10 else 0
    credits_validated = payload.credits_validated
    if credits_validated is None:
        credits_validated = credits_attempted if score is not None and score >= 10 else 0
    row = models.CourseEnrollment(
        **payload.model_dump(exclude={"credits_attempted", "credits_validated", "grade_point"}),
        credits_attempted=credits_attempted,
        credits_validated=credits_validated,
        grade_point=grade_point,
        school_id=school_id,
        registered_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("/students/{student_id}/lmd-summary", response_model=schemas.LmdSummaryResponse)
def lmd_summary(student_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_read(current_user, db)
    school_id = _school_id(current_user)
    student = db.query(models.StudentProfile).join(models.User).filter(models.StudentProfile.id == student_id, models.User.school_id == school_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    rows = db.query(models.CourseEnrollment).filter(models.CourseEnrollment.student_id == student_id, models.CourseEnrollment.school_id == school_id).all()
    attempted = sum(row.credits_attempted or 0 for row in rows)
    validated = sum(row.credits_validated or 0 for row in rows)
    weighted_points = sum((row.grade_point or 0) * (row.credits_attempted or 0) for row in rows)
    return {
        "student_id": student_id,
        "credits_attempted": attempted,
        "credits_validated": validated,
        "gpa": round(weighted_points / attempted, 2) if attempted else None,
        "completion_rate": round((validated / attempted) * 100, 2) if attempted else 0,
        "enrollments": rows,
    }

@router.get("/university-schedule", response_model=List[schemas.UniversityScheduleSlotResponse])
def list_university_schedule(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.UniversityScheduleSlot, current_user)
@router.post("/university-schedule", response_model=schemas.UniversityScheduleSlotResponse)
def create_university_schedule(payload: schemas.UniversityScheduleSlotCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.UniversityScheduleSlot, payload, current_user)

@router.get("/diplomas", response_model=List[schemas.DiplomaRecordResponse])
def list_diplomas(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.DiplomaRecord, current_user)
@router.post("/diplomas", response_model=schemas.DiplomaRecordResponse)
def create_diploma(payload: schemas.DiplomaRecordCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.DiplomaRecord, payload, current_user, {"issued_by_id": current_user.id})

@router.get("/transcripts", response_model=List[schemas.CertifiedTranscriptResponse])
def list_transcripts(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.CertifiedTranscript, current_user)
@router.post("/transcripts", response_model=schemas.CertifiedTranscriptResponse)
def create_transcript(payload: schemas.CertifiedTranscriptCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.CertifiedTranscript, payload, current_user, {"issued_by_id": current_user.id})

@router.get("/contracts", response_model=List[schemas.StaffContractResponse])
def list_contracts(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.StaffContract, current_user)
@router.post("/contracts", response_model=schemas.StaffContractResponse)
def create_contract(payload: schemas.StaffContractCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.StaffContract, payload, current_user)

@router.get("/leaves", response_model=List[schemas.LeaveRequestResponse])
def list_leaves(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.LeaveRequest, current_user)
@router.post("/leaves", response_model=schemas.LeaveRequestResponse)
def create_leave(payload: schemas.LeaveRequestCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.LeaveRequest, payload, current_user)

@router.post("/payroll-adjustments", response_model=schemas.PayrollAdjustmentResponse)
def create_payroll_adjustment(payload: schemas.PayrollAdjustmentCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _manager(current_user)
    payroll = db.query(models.PayrollRecord).filter(models.PayrollRecord.id == payload.payroll_record_id, models.PayrollRecord.school_id == _school_id(current_user)).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")
    row = models.PayrollAdjustment(**payload.model_dump())
    payroll.net_amount += payload.amount if payload.adjustment_type == "bonus" else -payload.amount
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("/transport-assignments", response_model=List[schemas.TransportAssignmentResponse])
def list_transport_assignments(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.TransportAssignment, current_user)
@router.post("/transport-assignments", response_model=schemas.TransportAssignmentResponse)
def create_transport_assignment(payload: schemas.TransportAssignmentCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.TransportAssignment, payload, current_user)

@router.get("/canteen-subscriptions", response_model=List[schemas.CanteenSubscriptionResponse])
def list_canteen_subscriptions(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.CanteenSubscription, current_user)
@router.post("/canteen-subscriptions", response_model=schemas.CanteenSubscriptionResponse)
def create_canteen_subscription(payload: schemas.CanteenSubscriptionCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.CanteenSubscription, payload, current_user)
@router.post("/canteen-attendance", response_model=schemas.CanteenAttendanceResponse)
def create_canteen_attendance(payload: schemas.CanteenAttendanceCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.CanteenAttendance, payload, current_user, {"served_by_id": current_user.id})

@router.get("/accounts", response_model=List[schemas.ChartAccountResponse])
def list_accounts(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.ChartAccount, current_user)
@router.post("/accounts", response_model=schemas.ChartAccountResponse)
def create_account(payload: schemas.ChartAccountCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.ChartAccount, payload, current_user)

@router.get("/vendor-invoices", response_model=List[schemas.VendorInvoiceResponse])
def list_vendor_invoices(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.VendorInvoice, current_user)
@router.post("/vendor-invoices", response_model=schemas.VendorInvoiceResponse)
def create_vendor_invoice(payload: schemas.VendorInvoiceCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.VendorInvoice, payload, current_user)

@router.get("/bank-transactions", response_model=List[schemas.BankTransactionResponse])
def list_bank_transactions(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.BankTransaction, current_user)
@router.post("/bank-transactions", response_model=schemas.BankTransactionResponse)
def create_bank_transaction(payload: schemas.BankTransactionCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.BankTransaction, payload, current_user)

@router.get("/journal-entries", response_model=List[schemas.JournalEntryResponse])
def list_journal_entries(start_date: Optional[str] = None, end_date: Optional[str] = None, account_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_read(current_user, db)
    school_id = _school_id(current_user)
    query = db.query(models.JournalEntry).options(selectinload(models.JournalEntry.lines)).filter(models.JournalEntry.school_id == school_id)
    if start_date:
        query = query.filter(models.JournalEntry.entry_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(models.JournalEntry.entry_date <= datetime.fromisoformat(end_date))
    if account_id:
        query = query.join(models.JournalLine).filter(models.JournalLine.account_id == account_id)
    return query.order_by(models.JournalEntry.entry_date.desc(), models.JournalEntry.id.desc()).all()

@router.post("/journal-entries", response_model=schemas.JournalEntryResponse)
def create_journal_entry(payload: schemas.JournalEntryCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_write(current_user, db)
    school_id = _school_id(current_user)
    debit = sum(line.debit for line in payload.lines)
    credit = sum(line.credit for line in payload.lines)
    if round(debit, 2) != round(credit, 2):
        raise HTTPException(status_code=400, detail="Journal entry must be balanced")
    entry = models.JournalEntry(
        entry_date=payload.entry_date,
        reference=payload.reference,
        description=payload.description,
        source_type=payload.source_type,
        source_id=payload.source_id,
        school_id=school_id,
        created_by_id=current_user.id,
    )
    for line in payload.lines:
        _ensure_school_row(db, models.ChartAccount, line.account_id, school_id, "Account")
        entry.lines.append(models.JournalLine(**line.model_dump(), school_id=school_id))
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@router.get("/ledger")
def general_ledger(account_id: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_read(current_user, db)
    school_id = _school_id(current_user)
    query = db.query(models.JournalLine, models.JournalEntry, models.ChartAccount).join(models.JournalEntry).join(models.ChartAccount).filter(models.JournalLine.school_id == school_id)
    if account_id:
        query = query.filter(models.JournalLine.account_id == account_id)
    balance = 0.0
    rows = []
    for line, entry, account in query.order_by(models.JournalEntry.entry_date, models.JournalEntry.id).all():
        balance += (line.debit or 0) - (line.credit or 0)
        rows.append({
            "entry_id": entry.id,
            "date": entry.entry_date,
            "reference": entry.reference,
            "account_code": account.code,
            "account_name": account.name,
            "label": line.label or entry.description,
            "debit": line.debit,
            "credit": line.credit,
            "running_balance": round(balance, 2),
        })
    return rows

@router.get("/trial-balance")
def trial_balance(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_read(current_user, db)
    school_id = _school_id(current_user)
    rows = db.query(
        models.ChartAccount.id,
        models.ChartAccount.code,
        models.ChartAccount.name,
        models.ChartAccount.account_type,
        func.coalesce(func.sum(models.JournalLine.debit), 0).label("debit"),
        func.coalesce(func.sum(models.JournalLine.credit), 0).label("credit"),
    ).outerjoin(models.JournalLine, models.JournalLine.account_id == models.ChartAccount.id).filter(
        models.ChartAccount.school_id == school_id
    ).group_by(models.ChartAccount.id).order_by(models.ChartAccount.code).all()
    accounts = [
        {
            "account_id": row.id,
            "code": row.code,
            "name": row.name,
            "type": row.account_type,
            "debit": row.debit,
            "credit": row.credit,
            "balance": round(row.debit - row.credit, 2),
        }
        for row in rows
    ]
    return {
        "accounts": accounts,
        "total_debit": sum(row["debit"] for row in accounts),
        "total_credit": sum(row["credit"] for row in accounts),
    }

@router.post("/bank-reconciliations", response_model=schemas.BankReconciliationResponse)
def create_bank_reconciliation(payload: schemas.BankReconciliationCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_write(current_user, db)
    school_id = _school_id(current_user)
    _ensure_school_row(db, models.BankTransaction, payload.bank_transaction_id, school_id, "Bank transaction")
    if payload.journal_entry_id:
        _ensure_school_row(db, models.JournalEntry, payload.journal_entry_id, school_id, "Journal entry")
    row = models.BankReconciliation(**payload.model_dump(), school_id=school_id, reconciled_by_id=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("/payroll-summary")
def payroll_summary(period: Optional[str] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _enterprise_read(current_user, db)
    school_id = _school_id(current_user)
    query = db.query(models.PayrollRecord).filter(models.PayrollRecord.school_id == school_id)
    if period:
        query = query.filter(models.PayrollRecord.period == period)
    records = query.all()
    adjustments = db.query(models.PayrollAdjustment).join(models.PayrollRecord).filter(models.PayrollRecord.school_id == school_id).all()
    return {
        "period": period,
        "records": len(records),
        "gross": sum(row.gross_amount for row in records),
        "deductions": sum(row.deductions for row in records),
        "net": sum(row.net_amount for row in records),
        "bonuses": sum(adj.amount for adj in adjustments if adj.adjustment_type == "bonus"),
        "retentions": sum(adj.amount for adj in adjustments if adj.adjustment_type != "bonus"),
    }

@router.post("/government-exports", response_model=schemas.GovernmentExportResponse)
def create_government_export(payload: schemas.GovernmentExportCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _manager(current_user)
    school_id = _school_id(current_user)
    export_payload = {
        "students": db.query(models.StudentProfile).join(models.User).filter(models.User.school_id == school_id).count(),
        "teachers": db.query(models.User).filter(models.User.school_id == school_id, models.User.role == models.UserRole.TEACHER).count(),
        "classes": db.query(models.Class).filter(models.Class.school_id == school_id).count(),
        "programs": db.query(models.AcademicProgram).filter(models.AcademicProgram.school_id == school_id).count(),
        "period": payload.period,
    }
    row = models.GovernmentExport(export_type=payload.export_type, period=payload.period, payload=export_payload, generated_by_id=current_user.id, school_id=school_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("/government-exports", response_model=List[schemas.GovernmentExportResponse])
def list_government_exports(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.GovernmentExport, current_user)

@router.post("/notification-providers", response_model=schemas.NotificationProviderResponse)
def create_notification_provider(payload: schemas.NotificationProviderCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _manager(current_user)
    row = models.NotificationProvider(
        **payload.model_dump(exclude={"api_key_secret"}),
        api_key_secret=crypto_utils.encrypt_secret(payload.api_key_secret),
        school_id=_school_id(current_user),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "channel": row.channel,
        "provider_name": row.provider_name,
        "api_key_secret": crypto_utils.mask_secret(row.api_key_secret),
        "sender_id": row.sender_id,
        "is_active": row.is_active,
        "school_id": row.school_id,
    }

@router.post("/notifications", response_model=schemas.NotificationMessageResponse)
def send_notification(payload: schemas.NotificationMessageCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _manager(current_user)
    provider = None
    if payload.provider_id:
        provider = db.query(models.NotificationProvider).filter(models.NotificationProvider.id == payload.provider_id, models.NotificationProvider.school_id == _school_id(current_user)).first()
        if not provider:
            raise HTTPException(status_code=404, detail="Notification provider not found")
    status, response = dispatch_notification(provider, payload)
    row = models.NotificationMessage(**payload.model_dump(), status=status, provider_response=response, school_id=_school_id(current_user), created_by_id=current_user.id, sent_at=datetime.utcnow() if status == models.NotificationStatus.SENT else None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("/notifications", response_model=List[schemas.NotificationMessageResponse])
def list_notifications(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _list(db, models.NotificationMessage, current_user)

@router.get("/direction-dashboard")
def direction_dashboard(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _manager(current_user)
    school_id = _school_id(current_user)
    revenue = db.query(func.coalesce(func.sum(models.Payment.amount), 0)).join(models.Fee).filter(models.Fee.school_id == school_id).scalar()
    expected = db.query(func.coalesce(func.sum(models.Fee.amount), 0)).filter(models.Fee.school_id == school_id).scalar()
    expenses = db.query(func.coalesce(func.sum(models.Expense.amount), 0)).filter(models.Expense.school_id == school_id).scalar()
    return {
        "students": db.query(models.StudentProfile).join(models.User).filter(models.User.school_id == school_id).count(),
        "teachers": db.query(models.User).filter(models.User.school_id == school_id, models.User.role == models.UserRole.TEACHER).count(),
        "classes": db.query(models.Class).filter(models.Class.school_id == school_id).count(),
        "programs": db.query(models.AcademicProgram).filter(models.AcademicProgram.school_id == school_id).count(),
        "revenue": revenue,
        "expected_revenue": expected,
        "outstanding": max(expected - revenue, 0),
        "expenses": expenses,
        "net": revenue - expenses,
        "pending_approvals": db.query(models.ApprovalWorkflow).filter(models.ApprovalWorkflow.school_id == school_id, models.ApprovalWorkflow.status == models.ApprovalStatus.PENDING).count(),
        "pending_admissions": db.query(models.AdmissionApplication).filter(models.AdmissionApplication.school_id == school_id, models.AdmissionApplication.status == models.AdmissionStatus.SUBMITTED).count(),
        "low_stock_items": db.query(models.InventoryItem).filter(models.InventoryItem.school_id == school_id, models.InventoryItem.status != models.InventoryStatus.AVAILABLE).count(),
    }

@router.get("/direction-dashboard/advanced")
def advanced_direction_dashboard(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    class_id: Optional[int] = None,
    level: Optional[str] = None,
    program_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    _enterprise_read(current_user, db)
    _manager(current_user)
    school_id = _school_id(current_user)
    payment_query = db.query(models.Payment, models.Fee, models.StudentProfile, models.Class).join(models.Fee).outerjoin(models.StudentProfile, models.Fee.student_id == models.StudentProfile.id).outerjoin(models.Class, models.StudentProfile.current_class_id == models.Class.id).filter(models.Fee.school_id == school_id)
    if start_date:
        payment_query = payment_query.filter(models.Payment.payment_date >= datetime.fromisoformat(start_date))
    if end_date:
        payment_query = payment_query.filter(models.Payment.payment_date <= datetime.fromisoformat(end_date))
    if class_id:
        payment_query = payment_query.filter((models.Fee.class_id == class_id) | (models.StudentProfile.current_class_id == class_id))
    if level:
        payment_query = payment_query.filter((models.Fee.level == level) if hasattr(models.Fee, "level") else models.Class.level == level)
    if operator_id:
        payment_query = payment_query.filter(models.Payment.recorded_by_id == operator_id)
    by_class = {}
    by_fee = {}
    by_operator = {}
    for payment, fee, _student, class_ in payment_query.all():
        class_name = class_.name if class_ else "Sans classe"
        by_class[class_name] = by_class.get(class_name, 0) + payment.amount
        category = fee.category or fee.title
        by_fee[category] = by_fee.get(category, 0) + payment.amount
        operator = str(payment.recorded_by_id or "Non renseigne")
        by_operator[operator] = by_operator.get(operator, 0) + payment.amount
    admission_query = db.query(models.AdmissionApplication).filter(models.AdmissionApplication.school_id == school_id)
    if program_id:
        admission_query = admission_query.filter(models.AdmissionApplication.desired_program_id == program_id)
    return {
        "filters": {"start_date": start_date, "end_date": end_date, "class_id": class_id, "level": level, "program_id": program_id, "operator_id": operator_id},
        "finance": {"by_class": by_class, "by_fee": by_fee, "by_operator": by_operator, "total": sum(by_fee.values())},
        "admissions": {
            "total": admission_query.count(),
            "submitted": admission_query.filter(models.AdmissionApplication.status == models.AdmissionStatus.SUBMITTED).count(),
            "accepted": admission_query.filter(models.AdmissionApplication.status == models.AdmissionStatus.ACCEPTED).count(),
            "enrolled": admission_query.filter(models.AdmissionApplication.status == models.AdmissionStatus.ENROLLED).count(),
        },
        "accounting": trial_balance(db, current_user),
        "hr": payroll_summary(None, db, current_user),
    }
