"""Diploma & certificate templates — `/document-templates`.

Per-school (multi-tenant) template management: CRUD, duplicate, activate,
set-default, background upload (PDF/DOCX/PNG/JPG via the existing secure
file-storage service), live preview (sample data, PREVIEW watermark, never
registered) and generation (real student data, registered in the universal
DocumentRegistry and stamped with the authenticity QR → verifiable at
`/verify/{uuid}`).

RBAC: admin / direction / secretary manage and generate; every mutation is
audit-logged (see services/document_templates.py).
"""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import database, models, schemas, security
from ..services import document_templates as svc
from ..services import file_storage

router = APIRouter(prefix="/document-templates", tags=["Document templates"])

_MANAGE_ROLES = (
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTOR,
)

_ALLOWED_EXTENSIONS = {".pdf": "pdf", ".docx": "docx", ".png": "png", ".jpg": "jpg", ".jpeg": "jpg"}


def _ensure_manage(current_user: models.User) -> None:
    if current_user.role not in _MANAGE_ROLES:
        raise HTTPException(status_code=403, detail="Réservé à l'administration / direction.")


def _school_id(current_user: models.User, school_id: Optional[int]) -> int:
    if current_user.role == models.UserRole.SUPER_ADMIN:
        if not school_id:
            raise HTTPException(status_code=400, detail="school_id requis pour le Super Admin.")
        return school_id
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Contexte d'établissement requis.")
    return current_user.school_id


def _template(db: Session, resolved: int, template_id: int) -> models.DocumentTemplate:
    tpl = svc.get_template(db, resolved, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    return tpl


def _school(db: Session, resolved: int) -> models.School:
    school = db.query(models.School).filter(models.School.id == resolved).first()
    if not school:
        raise HTTPException(status_code=404, detail="Établissement introuvable.")
    return school


def _pdf_response(pdf: bytes, filename: str) -> Response:
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/placeholders")
def list_placeholders(current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    return {"placeholders": svc.PLACEHOLDERS}


@router.get("", response_model=List[schemas.DocumentTemplateResponse])
def list_templates(kind: Optional[str] = None, school_id: Optional[int] = None,
                   db: Session = Depends(database.get_db),
                   current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    return svc.list_templates(db, resolved, kind=kind)


@router.post("", response_model=schemas.DocumentTemplateResponse)
def create_template(payload: schemas.DocumentTemplateCreate, school_id: Optional[int] = None,
                    db: Session = Depends(database.get_db),
                    current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    try:
        tpl = svc.create_template(db, resolved, payload.model_dump(exclude_unset=True), current_user)
    except ValueError:
        raise HTTPException(status_code=422, detail="kind doit être 'diploma' ou 'certificate'.")
    db.commit()
    db.refresh(tpl)
    return tpl


@router.patch("/{template_id}", response_model=schemas.DocumentTemplateResponse)
def update_template(template_id: int, payload: schemas.DocumentTemplateUpdate,
                    school_id: Optional[int] = None, db: Session = Depends(database.get_db),
                    current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    tpl = svc.update_template(db, _template(db, resolved, template_id),
                              payload.model_dump(exclude_unset=True), current_user)
    db.commit()
    db.refresh(tpl)
    return tpl


@router.delete("/{template_id}")
def delete_template(template_id: int, school_id: Optional[int] = None,
                    db: Session = Depends(database.get_db),
                    current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    svc.delete_template(db, _template(db, resolved, template_id), current_user)
    db.commit()
    return {"deleted": True}


@router.post("/{template_id}/duplicate", response_model=schemas.DocumentTemplateResponse)
def duplicate_template(template_id: int, school_id: Optional[int] = None,
                       db: Session = Depends(database.get_db),
                       current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    copy = svc.duplicate_template(db, _template(db, resolved, template_id), current_user)
    db.commit()
    db.refresh(copy)
    return copy


@router.post("/{template_id}/default", response_model=schemas.DocumentTemplateResponse)
def set_default_template(template_id: int, school_id: Optional[int] = None,
                         db: Session = Depends(database.get_db),
                         current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    tpl = svc.set_default(db, _template(db, resolved, template_id), current_user)
    db.commit()
    db.refresh(tpl)
    return tpl


@router.post("/{template_id}/background", response_model=schemas.DocumentTemplateResponse)
async def upload_background(template_id: int, file: UploadFile = File(...),
                            school_id: Optional[int] = None,
                            db: Session = Depends(database.get_db),
                            current_user: models.User = Depends(security.get_current_user)):
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    tpl = _template(db, resolved, template_id)
    extension = Path(file.filename or "").suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Formats acceptés : PDF, DOCX, PNG, JPG.")
    metadata = await file_storage.store_upload(file, resolved, user_id=current_user.id, folder="templates")
    tpl.background_path = metadata["storage_path"]
    tpl.background_type = _ALLOWED_EXTENSIONS[extension]
    tpl.background_filename = file.filename
    db.commit()
    db.refresh(tpl)
    return tpl


@router.post("/{template_id}/preview")
def preview_template(template_id: int, payload: schemas.DocumentPreviewRequest,
                     school_id: Optional[int] = None, db: Session = Depends(database.get_db),
                     current_user: models.User = Depends(security.get_current_user)):
    """Sample-data preview with a PREVIEW watermark — never registered, no QR."""
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    tpl = _template(db, resolved, template_id)
    school = _school(db, resolved)
    overrides = {**svc.SAMPLE_FIELDS, **(payload.overrides or {})}
    fields = svc.resolve_fields(db, school, None, tpl.kind, overrides)
    pdf = svc.render_pdf(tpl, tpl.kind, fields, None, watermark="APERÇU / PREVIEW")
    return _pdf_response(pdf, f"preview-{tpl.kind}-{tpl.id}.pdf")


@router.post("/generate")
def generate_document(payload: schemas.DocumentGenerateRequest, school_id: Optional[int] = None,
                      db: Session = Depends(database.get_db),
                      current_user: models.User = Depends(security.get_current_user)):
    """Generate a diploma/certificate for a real student using the requested
    template (or the school's default for the kind), register it in the
    document registry and return the QR-stamped PDF."""
    _ensure_manage(current_user)
    resolved = _school_id(current_user, school_id)
    school = _school(db, resolved)

    tpl: Optional[models.DocumentTemplate] = None
    kind = payload.kind
    if payload.template_id:
        tpl = _template(db, resolved, payload.template_id)
        kind = tpl.kind
    elif kind in svc.KINDS:
        tpl = svc.default_template(db, resolved, kind)
    if kind not in svc.KINDS:
        raise HTTPException(status_code=422, detail="kind doit être 'diploma' ou 'certificate'.")

    profile = (
        db.query(models.StudentProfile)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(models.StudentProfile.id == payload.student_id,
                models.User.school_id == resolved)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Élève introuvable dans cet établissement.")

    pdf, row = svc.generate(db, school, tpl, kind, profile, current_user, payload.overrides)
    db.commit()
    return _pdf_response(pdf, f"{kind}-{row.reference or row.uuid}.pdf")
