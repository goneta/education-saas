"""Human Resources — staff leave self-service + approval workflow (Slice 5,
Loop 8 gap).

Builds on the existing `models.LeaveRequest` (also exposed via the admin
`/enterprise/leaves` endpoints) rather than duplicating it. The new value here is
self-service submission (staff_user_id taken from the caller), own/all list
scoping, and the approve/reject decision workflow with notification.
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security
from ..services import automation

router = APIRouter(prefix="/hr", tags=["Human Resources"])

APPROVER_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


@router.get("/leave-requests", response_model=List[schemas.LeaveRequestResponse])
def list_leave_requests(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Administrators see every request in the school; other staff see only theirs."""
    school_id = _school_id(current_user)
    query = db.query(models.LeaveRequest).filter(models.LeaveRequest.school_id == school_id)
    if current_user.role not in APPROVER_ROLES:
        query = query.filter(models.LeaveRequest.staff_user_id == current_user.id)
    return query.order_by(models.LeaveRequest.id.desc()).all()


@router.post("/leave-requests", response_model=schemas.LeaveRequestResponse)
def create_leave_request(payload: schemas.LeaveSelfRequestCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Self-service: any authenticated staff member submits a request for themselves."""
    school_id = _school_id(current_user)
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="La date de fin précède la date de début")
    row = models.LeaveRequest(
        staff_user_id=current_user.id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
        status=models.LeaveStatus.PENDING,
        school_id=school_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/leave-requests/{request_id}/decide", response_model=schemas.LeaveRequestResponse)
def decide_leave_request(request_id: int, payload: schemas.LeaveDecision, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Approve or reject a request (administrators only); notifies the requester."""
    if current_user.role not in APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")
    decision = payload.status.lower()
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Décision invalide")
    school_id = _school_id(current_user)
    row = db.query(models.LeaveRequest).filter(models.LeaveRequest.id == request_id, models.LeaveRequest.school_id == school_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    row.status = models.LeaveStatus.APPROVED if decision == "approved" else models.LeaveStatus.REJECTED
    row.decided_by_id = current_user.id
    staff = db.query(models.User).filter(models.User.id == row.staff_user_id).first()
    automation.record_notification(
        db,
        event_type="hr.leave_decided",
        subject="Demande de congé",
        message=f"Votre demande de congé ({row.leave_type}) a été {('approuvée' if decision == 'approved' else 'refusée')}.",
        school_id=school_id,
        recipient_user=staff,
        source_type="leave_request",
        source_id=row.id,
        current_user=current_user,
    )
    db.commit()
    db.refresh(row)
    return row
