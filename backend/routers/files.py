from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import database, models, rbac, schemas, security
from ..services import file_storage


router = APIRouter(prefix="/files", tags=["Secure Files"])


def _school_scope(current_user: models.User) -> int | None:
    return current_user.school_id


def _query_file(db: Session, file_id: int, current_user: models.User) -> models.SecureFile:
    query = db.query(models.SecureFile).filter(models.SecureFile.id == file_id, models.SecureFile.status == "active")
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.SecureFile.school_id == current_user.school_id)
    row = query.first()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return row


@router.post("/", response_model=schemas.SecureFileResponse)
async def upload_file(
    file: UploadFile = File(...),
    entity_type: Optional[str] = Form(default=None),
    entity_id: Optional[str] = Form(default=None),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "files:write", db)
    metadata = await file_storage.store_upload(file, _school_scope(current_user))
    row = models.SecureFile(
        **metadata,
        entity_type=entity_type,
        entity_id=entity_id,
        school_id=_school_scope(current_user),
        uploaded_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/", response_model=List[schemas.SecureFileResponse])
def list_files(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "files:read", db)
    query = db.query(models.SecureFile).filter(models.SecureFile.status == "active")
    if current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(models.SecureFile.school_id == current_user.school_id)
    if entity_type:
        query = query.filter(models.SecureFile.entity_type == entity_type)
    if entity_id:
        query = query.filter(models.SecureFile.entity_id == entity_id)
    return query.order_by(models.SecureFile.created_at.desc()).limit(min(limit, 500)).all()


@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "files:read", db)
    row = _query_file(db, file_id, current_user)
    path = file_storage.open_stored_file(row.storage_path)
    return FileResponse(path, media_type=row.content_type, filename=row.original_filename)


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "files:delete", db)
    row = _query_file(db, file_id, current_user)
    row.status = "deleted"
    row.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "File deleted"}
