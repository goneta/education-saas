"""Vie scolaire — Discipline, Examens, Activités, Santé scolaire, Internat.

FIVE modules through ONE factorized CRUD engine (`_register_module`): each
module declares its model, writable fields and options; the engine provides
the identical surface everywhere — list (search / status & type filters /
skip-limit pagination), detail, create, update, delete, CSV export — with
tenant scoping (rows always school-scoped to the caller), role-gated writes,
and an audit record for every mutation. Type codes come from the hierarchical
reference lists (global TeducAI + school-local, services/reference_data.py).

Permissions:
- writes: SUPER_ADMIN / SCHOOL_ADMIN / DIRECTION everywhere;
- reads: any authenticated member of the school — EXCEPT Santé scolaire
  (sensitive medical data): reads are restricted to the write roles too.
"""

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import audit, database, models, security

router = APIRouter(prefix="/school-life", tags=["Vie scolaire"])

MANAGE_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
}

DATE_FIELDS = {"record_date", "exam_date", "start_date", "end_date", "follow_up_date"}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Contexte établissement requis.")
    return current_user.school_id


def _require_manage(current_user: models.User) -> None:
    if current_user.role not in MANAGE_ROLES:
        raise HTTPException(status_code=403, detail="Réservé à l'administration (admin / direction).")


def _student_name(row) -> Optional[str]:
    student = getattr(row, "student", None)
    return student.user.full_name if student and student.user else None


def _coerce(field: str, value):
    if value is None or value == "":
        return None
    if field in DATE_FIELDS and isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Date invalide pour « {field} ».")
    return value


def _serialize(row, fields: list[str]) -> dict:
    data = {"id": row.id, "school_id": row.school_id}
    for field in fields:
        value = getattr(row, field, None)
        data[field] = value.isoformat() if isinstance(value, datetime) else value
    data["student_name"] = _student_name(row)
    data["created_at"] = row.created_at.isoformat() if row.created_at else None
    return data


def _validate_student(db: Session, school_id: int, student_id) -> None:
    if student_id is None:
        return
    profile = (
        db.query(models.StudentProfile)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(models.StudentProfile.id == student_id, models.User.school_id == school_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Élève introuvable dans votre établissement.")


def _register_module(
    *,
    slug: str,
    model,
    fields: list[str],
    required: list[str],
    search_fields: list[str],
    type_field: Optional[str],
    restricted_read: bool = False,
    export_headers: Optional[list[str]] = None,
):
    """Mount the uniform CRUD surface for one module under /school-life/{slug}."""

    def _read_guard(current_user: models.User) -> int:
        if restricted_read:
            _require_manage(current_user)
        return _school_id(current_user)

    def _get_or_404(db: Session, current_user: models.User, item_id: int):
        row = db.query(model).filter(model.id == item_id, model.school_id == _school_id(current_user)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Enregistrement introuvable.")
        return row

    def _base_query(db: Session, school_id: int, search: Optional[str], status: Optional[str],
                    type_code: Optional[str], student_id: Optional[int]):
        query = db.query(model).filter(model.school_id == school_id)
        if status:
            query = query.filter(model.status == status)
        if type_code and type_field:
            query = query.filter(getattr(model, type_field) == type_code)
        if student_id is not None and hasattr(model, "student_id"):
            query = query.filter(model.student_id == student_id)
        if search:
            pattern = f"%{search}%"
            clauses = [getattr(model, field).ilike(pattern) for field in search_fields]
            if hasattr(model, "student_id"):
                clauses.append(
                    model.student_id.in_(
                        db.query(models.StudentProfile.id)
                        .join(models.User, models.User.id == models.StudentProfile.user_id)
                        .filter(models.User.full_name.ilike(pattern))
                    )
                )
            query = query.filter(or_(*clauses))
        return query.order_by(model.id.desc())

    @router.get(f"/{slug}")
    def list_items(
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        status: Optional[str] = None,
        type_code: Optional[str] = None,
        student_id: Optional[int] = None,
        current_user: models.User = Depends(security.get_current_user),
        db: Session = Depends(database.get_db),
    ):
        school_id = _read_guard(current_user)
        query = _base_query(db, school_id, search, status, type_code, student_id)
        total = query.count()
        rows = query.offset(max(skip, 0)).limit(min(max(limit, 1), 200)).all()
        return {"total": total, "items": [_serialize(row, fields) for row in rows]}

    @router.get(f"/{slug}/export.csv")
    def export_csv(
        search: Optional[str] = None,
        status: Optional[str] = None,
        type_code: Optional[str] = None,
        current_user: models.User = Depends(security.get_current_user),
        db: Session = Depends(database.get_db),
    ):
        school_id = _read_guard(current_user)
        rows = _base_query(db, school_id, search, status, type_code, None).limit(10000).all()
        headers = export_headers or (["id", "student_name"] + fields + ["created_at"])
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(_serialize(row, fields))
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={slug}.csv"},
        )

    @router.get(f"/{slug}/{{item_id}}")
    def get_item(
        item_id: int,
        current_user: models.User = Depends(security.get_current_user),
        db: Session = Depends(database.get_db),
    ):
        _read_guard(current_user)
        return _serialize(_get_or_404(db, current_user, item_id), fields)

    @router.post(f"/{slug}")
    def create_item(
        payload: dict,
        current_user: models.User = Depends(security.get_current_user),
        db: Session = Depends(database.get_db),
    ):
        _require_manage(current_user)
        school_id = _school_id(current_user)
        for field in required:
            if payload.get(field) in (None, ""):
                raise HTTPException(status_code=422, detail=f"Le champ « {field} » est obligatoire.")
        if "student_id" in fields:
            _validate_student(db, school_id, payload.get("student_id"))
        row = model(school_id=school_id)
        for field in fields:
            if field in payload:
                setattr(row, field, _coerce(field, payload.get(field)))
        if hasattr(row, "created_by_id"):
            row.created_by_id = current_user.id
        if hasattr(row, "decided_by_id") and not payload.get("decided_by_id"):
            row.decided_by_id = current_user.id
        db.add(row)
        db.flush()
        audit.record_audit(db, action=f"school_life.{slug}.created", current_user=current_user,
                           entity_type=slug, entity_id=row.id)
        db.commit()
        db.refresh(row)
        return _serialize(row, fields)

    @router.patch(f"/{slug}/{{item_id}}")
    def update_item(
        item_id: int,
        payload: dict,
        current_user: models.User = Depends(security.get_current_user),
        db: Session = Depends(database.get_db),
    ):
        _require_manage(current_user)
        row = _get_or_404(db, current_user, item_id)
        if "student_id" in payload and "student_id" in fields:
            _validate_student(db, row.school_id, payload.get("student_id"))
        for field in fields:
            if field in payload:
                setattr(row, field, _coerce(field, payload.get(field)))
        audit.record_audit(db, action=f"school_life.{slug}.updated", current_user=current_user,
                           entity_type=slug, entity_id=row.id)
        db.commit()
        db.refresh(row)
        return _serialize(row, fields)

    @router.delete(f"/{slug}/{{item_id}}")
    def delete_item(
        item_id: int,
        current_user: models.User = Depends(security.get_current_user),
        db: Session = Depends(database.get_db),
    ):
        _require_manage(current_user)
        row = _get_or_404(db, current_user, item_id)
        audit.record_audit(db, action=f"school_life.{slug}.deleted", current_user=current_user,
                           entity_type=slug, entity_id=row.id)
        db.delete(row)
        db.commit()
        return {"status": "deleted"}


_register_module(
    slug="discipline",
    model=models.DisciplineRecord,
    fields=["student_id", "record_kind", "type_code", "title", "description", "record_date", "status"],
    required=["student_id", "record_kind", "title"],
    search_fields=["title", "description"],
    type_field="type_code",
)

_register_module(
    slug="exams",
    # REUSES the existing exam_sessions table (legacy operations planning),
    # extended column-only in migration 0056 — zero duplication.
    model=models.ExamSession,
    fields=["name", "exam_type", "class_id", "subject_id", "start_date", "end_date",
            "duration_minutes", "room", "max_score", "coefficient", "status", "notes"],
    required=["name", "exam_type"],
    search_fields=["name", "notes"],
    type_field="exam_type",
)

_register_module(
    slug="activities",
    model=models.SchoolActivity,
    fields=["name", "activity_type_code", "description", "location", "start_date", "end_date",
            "class_id", "capacity", "fee_amount", "status"],
    required=["name"],
    search_fields=["name", "description", "location"],
    type_field="activity_type_code",
)

_register_module(
    slug="health",
    model=models.HealthRecord,
    fields=["student_id", "record_type_code", "title", "details", "record_date", "severity",
            "treated_by", "follow_up_date", "is_confidential", "status"],
    required=["student_id", "title"],
    search_fields=["title", "details"],
    type_field="record_type_code",
    restricted_read=True,  # medical data: administration only, reads included
)

_register_module(
    slug="boarding",
    model=models.BoardingRecord,
    fields=["student_id", "room_id", "start_date", "end_date", "status", "notes"],
    required=["student_id"],
    search_fields=["notes", "status"],
    type_field=None,
)
