"""Analytics & BI — tenant-scoped CSV export and AI-generated insights
(Slice 6, Loop 9 gaps). Dashboards/KPIs already live in `dashboard.py` and
`enterprise.py`; this adds machine-readable export and an AI narrative.
"""

import csv
import io
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import database, models, security
from ..services.ai_service import ai_service

router = APIRouter(prefix="/analytics", tags=["Analytics & BI"])

EXPORT_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.ACCOUNTANT,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _students_rows(db: Session, school_id: int):
    yield ["id", "full_name", "email", "registration_number"]
    rows = (
        db.query(models.User, models.StudentProfile)
        .join(models.StudentProfile, models.StudentProfile.user_id == models.User.id)
        .filter(models.User.school_id == school_id, models.User.role == models.UserRole.STUDENT)
        .all()
    )
    for user, profile in rows:
        yield [user.id, user.full_name, user.email, profile.registration_number]


def _teachers_rows(db: Session, school_id: int):
    yield ["id", "full_name", "email"]
    for user in db.query(models.User).filter(models.User.school_id == school_id, models.User.role == models.UserRole.TEACHER).all():
        yield [user.id, user.full_name, user.email]


def _fees_rows(db: Session, school_id: int):
    yield ["id", "title", "amount", "status", "category"]
    for fee in db.query(models.Fee).filter(models.Fee.school_id == school_id).all():
        yield [fee.id, fee.title, fee.amount, getattr(fee.status, "value", fee.status), fee.category]


DATASETS: dict[str, Callable] = {
    "students": _students_rows,
    "teachers": _teachers_rows,
    "fees": _fees_rows,
}


@router.get("/export/{dataset}")
def export_csv(dataset: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Export a tenant-scoped dataset as CSV (students/teachers/fees)."""
    if current_user.role not in EXPORT_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")
    builder = DATASETS.get(dataset)
    if not builder:
        raise HTTPException(status_code=404, detail="Dataset inconnu")
    school_id = _school_id(current_user)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    for row in builder(db, school_id):
        writer.writerow(row)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{dataset}.csv"'},
    )


@router.get("/insights")
def ai_insights(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """AI-generated narrative over the institution's headline KPIs. Degrades to
    the local fallback when no AI provider is configured."""
    if current_user.role not in EXPORT_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")
    school_id = _school_id(current_user)
    kpis = {
        "students": db.query(models.User).filter(models.User.school_id == school_id, models.User.role == models.UserRole.STUDENT).count(),
        "teachers": db.query(models.User).filter(models.User.school_id == school_id, models.User.role == models.UserRole.TEACHER).count(),
        "fees": db.query(models.Fee).filter(models.Fee.school_id == school_id).count(),
        "unpaid_fees": db.query(models.Fee).filter(models.Fee.school_id == school_id, models.Fee.status == models.FeeStatus.PENDING).count(),
    }
    prompt = (
        "You are an education-operations analyst. Given these institution KPIs, "
        f"write 3 short, concrete insights and 1 recommended action:\n{kpis}"
    )
    result = ai_service.generate_response_from_config(prompt, {"module": "analytics_insights"}, db)
    return {"kpis": kpis, "insights": result.get("message"), "details": result.get("data")}
