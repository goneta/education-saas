from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func
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


def _enforce_school_quota(db: Session, current_user: models.User, incoming_bytes: int) -> None:
    if current_user.role == models.UserRole.SUPER_ADMIN or not current_user.school_id:
        return
    school = db.query(models.School).filter(models.School.id == current_user.school_id).first()
    quota_mb = school.storage_quota_mb if school else 1024
    used = db.query(func.coalesce(func.sum(models.SecureFile.size_bytes), 0)).filter(
        models.SecureFile.school_id == current_user.school_id,
        models.SecureFile.status == "active",
    ).scalar() or 0
    if used + incoming_bytes > quota_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="School storage quota exceeded")


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
    _enforce_school_quota(db, current_user, metadata["size_bytes"])
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
    if row.storage_backend in {"s3", "minio"}:
        url = file_storage.signed_download_url(row.storage_backend, row.storage_path, row.content_type, row.original_filename)
        if url:
            return {"signed_url": url, "expires_in": file_storage.SIGNED_URL_EXPIRES_SECONDS}
    path = file_storage.open_stored_file(row.storage_path)
    return FileResponse(path, media_type=row.content_type, filename=row.original_filename)


@router.get("/{file_id}/signed-url")
def signed_file_url(
    file_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "files:read", db)
    row = _query_file(db, file_id, current_user)
    url = file_storage.signed_download_url(row.storage_backend, row.storage_path, row.content_type, row.original_filename)
    if not url:
        return {"signed_url": f"/files/{row.id}/download", "expires_in": None}
    return {"signed_url": url, "expires_in": file_storage.SIGNED_URL_EXPIRES_SECONDS}


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
