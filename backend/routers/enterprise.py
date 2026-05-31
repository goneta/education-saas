from datetime import datetime
from typing import List, Type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(prefix="/enterprise", tags=["Enterprise"])

MANAGER_ROLES = {models.UserRole.SUPER_ADMIN, models.UserRole.SCHOOL_ADMIN, models.UserRole.DIRECTION, models.UserRole.REGISTRAR}


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


@router.get("/approvals", response_model=List[schemas.ApprovalWorkflowResponse])
def list_approvals(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.ApprovalWorkflow).filter(models.ApprovalWorkflow.school_id == _school_id(current_user)).order_by(models.ApprovalWorkflow.created_at.desc()).all()


@router.post("/approvals", response_model=schemas.ApprovalWorkflowResponse)
def create_approval(workflow: schemas.ApprovalWorkflowCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _manager(current_user)
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
    workflow = db.query(models.ApprovalWorkflow).filter(models.ApprovalWorkflow.id == workflow_id, models.ApprovalWorkflow.school_id == _school_id(current_user)).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    step = db.query(models.ApprovalStep).filter(models.ApprovalStep.workflow_id == workflow.id, models.ApprovalStep.step_order == workflow.current_step).first()
    if not step or step.role != current_user.role:
        raise HTTPException(status_code=403, detail="Current step is assigned to another role")
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
def create_notification_provider(payload: schemas.NotificationProviderCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)): return _create(db, models.NotificationProvider, payload, current_user)

@router.post("/notifications", response_model=schemas.NotificationMessageResponse)
def send_notification(payload: schemas.NotificationMessageCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _manager(current_user)
    provider = None
    if payload.provider_id:
        provider = db.query(models.NotificationProvider).filter(models.NotificationProvider.id == payload.provider_id, models.NotificationProvider.school_id == _school_id(current_user)).first()
    status = models.NotificationStatus.SENT if provider and provider.api_key_secret else models.NotificationStatus.QUEUED
    response = "Provider configured; marked sent." if status == models.NotificationStatus.SENT else "Queued: configure provider API key for real delivery."
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
