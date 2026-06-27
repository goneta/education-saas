import secrets
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .. import audit, database, models, rbac, schemas, security
from ..services import file_storage


router = APIRouter(prefix="/files", tags=["Secure Files"])


def _school_scope(current_user: models.User) -> int | None:
    return current_user.school_id


def _ensure_numref(db: Session, user: models.User | None) -> None:
    if not user or user.numref:
        return
    user.numref = f"USR-{datetime.now(timezone.utc).year}-{secrets.randbelow(1000000):06d}"
    db.commit()
    db.refresh(user)


def _query_file(db: Session, file_id: int, current_user: models.User) -> models.SecureFile:
    query = db.query(models.SecureFile).filter(models.SecureFile.id == file_id, models.SecureFile.status == "active")
    row = query.first()
    if not row or not _can_access_file(db, row, current_user):
        raise HTTPException(status_code=404, detail="File not found")
    return row


def _is_admin(current_user: models.User) -> bool:
    return current_user.role in {
        models.UserRole.SUPER_ADMIN,
        models.UserRole.SCHOOL_ADMIN,
        models.UserRole.ADMIN,
        models.UserRole.DIRECTION,
        models.UserRole.DIRECTOR,
        models.UserRole.PRINCIPAL,
        models.UserRole.SECRETARY,
    }


def _can_access_file(db: Session, row: models.SecureFile, current_user: models.User) -> bool:
    now = datetime.now(timezone.utc)
    if row.expires_at and row.expires_at.replace(tzinfo=timezone.utc) < now:
        return False
    if row.uploaded_by_id == current_user.id:
        return True
    if _is_admin(current_user) and (current_user.role == models.UserRole.SUPER_ADMIN or row.school_id == current_user.school_id):
        return True
    if row.visibility == "public_external" and row.approval_status == "approved":
        return True
    if row.visibility == "public_internal" and row.school_id == current_user.school_id and row.approval_status == "approved":
        return True
    share = db.query(models.DocumentShare).filter(
        models.DocumentShare.file_id == row.id,
        models.DocumentShare.status == "active",
        or_(
            models.DocumentShare.recipient_user_id == current_user.id,
            and_(models.DocumentShare.recipient_school_id == current_user.school_id, models.DocumentShare.recipient_school_id != None),
            models.DocumentShare.recipient_numref == current_user.numref,
        ),
    ).first()
    if not share:
        return False
    if share.expires_at and share.expires_at.replace(tzinfo=timezone.utc) < now:
        return False
    if share.download_limit is not None and share.download_count >= share.download_limit:
        return False
    return True


def _can_share_file(row: models.SecureFile, current_user: models.User, db: Session) -> bool:
    if row.uploaded_by_id == current_user.id or _is_admin(current_user):
        return True
    return db.query(models.DocumentShare).filter(
        models.DocumentShare.file_id == row.id,
        models.DocumentShare.recipient_user_id == current_user.id,
        models.DocumentShare.can_reshare == True,
        models.DocumentShare.status == "active",
    ).first() is not None


def _share_types_allowed(current_user: models.User) -> set[str]:
    if current_user.role in [models.UserRole.STUDENT, models.UserRole.PUPIL]:
        return {"B2P", "P2P"}
    return {"B2B", "B2P", "P2P"}


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
    document_name: Optional[str] = Form(default=None),
    category: Optional[str] = Form(default=None),
    visibility: str = Form(default="private"),
    is_shareable: bool = Form(default=False),
    entity_type: Optional[str] = Form(default=None),
    entity_id: Optional[str] = Form(default=None),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "files:create", db)
    _ensure_numref(db, current_user)
    clean_document_name = (document_name or "").strip() or file_storage.safe_original_filename(file.filename or "Document")
    metadata = await file_storage.store_upload(file, _school_scope(current_user), document_name=clean_document_name, user_id=current_user.id)
    _enforce_school_quota(db, current_user, metadata["size_bytes"])
    approval_status = "pending" if visibility in {"public_external", "public"} and current_user.role in [models.UserRole.STUDENT, models.UserRole.PUPIL] else "approved"
    row = models.SecureFile(
        **metadata,
        category=category,
        visibility="public_external" if visibility == "public" else visibility,
        is_shareable=is_shareable,
        approval_status=approval_status,
        approved_by_id=current_user.id if approval_status == "approved" else None,
        approved_at=datetime.now(timezone.utc) if approval_status == "approved" else None,
        entity_type=entity_type,
        entity_id=entity_id,
        school_id=_school_scope(current_user),
        uploaded_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    audit.record_audit(db, action="document.uploaded", current_user=current_user, entity_type="secure_file", entity_id=row.id, details={"visibility": row.visibility, "approval_status": row.approval_status})
    return row


@router.get("/", response_model=List[schemas.SecureFileResponse])
def list_files(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "files:view", db)
    _ensure_numref(db, current_user)
    query = db.query(models.SecureFile).filter(models.SecureFile.status == "active")
    if not _is_admin(current_user):
        owned_ids = db.query(models.SecureFile.id).filter(models.SecureFile.uploaded_by_id == current_user.id)
        shared_ids = db.query(models.DocumentShare.file_id).filter(
            models.DocumentShare.status == "active",
            or_(
                models.DocumentShare.recipient_user_id == current_user.id,
                models.DocumentShare.recipient_school_id == current_user.school_id,
                models.DocumentShare.recipient_numref == current_user.numref,
            ),
        )
        query = query.filter(or_(
            models.SecureFile.id.in_(owned_ids),
            models.SecureFile.id.in_(shared_ids),
            and_(models.SecureFile.visibility == "public_internal", models.SecureFile.school_id == current_user.school_id, models.SecureFile.approval_status == "approved"),
            and_(models.SecureFile.visibility == "public_external", models.SecureFile.approval_status == "approved"),
        ))
    elif current_user.role != models.UserRole.SUPER_ADMIN:
        query = query.filter(or_(models.SecureFile.school_id == current_user.school_id, models.SecureFile.visibility == "public_external"))
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
    rbac.require_permission(current_user, "files:download", db)
    row = _query_file(db, file_id, current_user)
    row.access_count += 1
    share = db.query(models.DocumentShare).filter(
        models.DocumentShare.file_id == row.id,
        models.DocumentShare.status == "active",
        models.DocumentShare.recipient_user_id == current_user.id,
    ).first()
    if share:
        share.download_count += 1
    audit.record_audit(db, action="document.downloaded", current_user=current_user, entity_type="secure_file", entity_id=row.id)
    db.commit()
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
    rbac.require_permission(current_user, "files:view", db)
    row = _query_file(db, file_id, current_user)
    url = file_storage.signed_download_url(row.storage_backend, row.storage_path, row.content_type, row.original_filename)
    if not url:
        return {"signed_url": f"/files/{row.id}/download", "expires_in": None}
    return {"signed_url": url, "expires_in": file_storage.SIGNED_URL_EXPIRES_SECONDS}


@router.get("/recipients/search", response_model=List[schemas.DocumentRecipientResponse])
def search_recipients(
    share_type: str = "B2P",
    numref: Optional[str] = None,
    role: Optional[str] = None,
    level: Optional[str] = None,
    class_id: Optional[int] = None,
    q: Optional[str] = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    _ensure_numref(db, current_user)
    if share_type not in _share_types_allowed(current_user):
        raise HTTPException(status_code=403, detail="This share type is not allowed for your role")
    rows: list[schemas.DocumentRecipientResponse] = []
    if share_type == "B2B":
        schools = db.query(models.School).filter(models.School.is_active == True)
        if current_user.school_id:
            schools = schools.filter(models.School.id != current_user.school_id)
        if q:
            schools = schools.filter(models.School.name.ilike(f"%{q}%"))
        for school in schools.limit(50).all():
            rows.append(schemas.DocumentRecipientResponse(id=school.id, type="school", name=school.name, school_id=school.id, school_name=school.name, subtitle=school.school_type.value if school.school_type else None))
        return rows
    users = db.query(models.User).filter(models.User.is_active == True)
    if numref:
        users = users.filter(models.User.numref == numref.strip())
    elif share_type == "B2P":
        users = users.filter(models.User.school_id == current_user.school_id)
        if role:
            users = users.filter(models.User.role == role)
        if q:
            users = users.filter(or_(models.User.full_name.ilike(f"%{q}%"), models.User.email.ilike(f"%{q}%")))
    else:
        users = users.filter(models.User.school_id == current_user.school_id, models.User.id != current_user.id)
        if q:
            users = users.filter(or_(models.User.full_name.ilike(f"%{q}%"), models.User.email.ilike(f"%{q}%")))
    if class_id or level:
        users = users.join(models.StudentProfile, models.StudentProfile.user_id == models.User.id)
        if class_id:
            users = users.filter(models.StudentProfile.current_class_id == class_id)
        if level:
            users = users.join(models.Class, models.StudentProfile.current_class_id == models.Class.id).filter(models.Class.level == level)
    found_users = users.limit(100).all()
    changed = False
    for user in found_users:
        if not user.numref:
            user.numref = f"USR-{datetime.now(timezone.utc).year}-{secrets.randbelow(1000000):06d}"
            changed = True
    if changed:
        db.commit()
    for user in found_users:
        rows.append(schemas.DocumentRecipientResponse(id=user.id, type="user", name=user.full_name or user.email, role=user.role.value, school_id=user.school_id, school_name=user.school.name if user.school else None, numref=user.numref, subtitle=user.email))
    return rows


@router.post("/share", response_model=List[schemas.DocumentShareResponse])
def share_document(
    payload: schemas.DocumentShareCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "files:share", db)
    _ensure_numref(db, current_user)
    if payload.share_type not in _share_types_allowed(current_user):
        raise HTTPException(status_code=403, detail="This share type is not allowed for your role")
    row = _query_file(db, payload.file_id, current_user)
    if not _can_share_file(row, current_user, db):
        raise HTTPException(status_code=403, detail="This document cannot be reshared")
    created = []
    user_ids = payload.recipient_user_ids[:]
    if payload.recipient_numrefs:
        users = db.query(models.User).filter(models.User.numref.in_(payload.recipient_numrefs)).all()
        user_ids.extend([user.id for user in users])
    for user_id in sorted(set(user_ids)):
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            continue
        share = models.DocumentShare(file_id=row.id, share_type=payload.share_type, mode=payload.mode, can_reshare=payload.can_reshare, recipient_user_id=user.id, recipient_numref=user.numref, encrypted_token=secrets.token_urlsafe(32), expires_at=payload.expires_at, download_limit=payload.download_limit, created_by_id=current_user.id, school_id=current_user.school_id)
        db.add(share)
        created.append(share)
        db.add(models.NotificationHistory(event_type="document.shared", recipient_user_id=user.id, recipient_name=user.full_name, recipient_contact=user.email, channel="system", subject="Document partagé", message=f"{current_user.full_name or current_user.email} a partagé un document avec vous.", source_type="secure_file", source_id=row.id, school_id=user.school_id or current_user.school_id, created_by_id=current_user.id))
    for school_id in payload.recipient_school_ids:
        school = db.query(models.School).filter(models.School.id == school_id, models.School.is_active == True).first()
        if not school:
            continue
        share = models.DocumentShare(file_id=row.id, share_type="B2B", mode=payload.mode, can_reshare=payload.can_reshare, recipient_school_id=school.id, encrypted_token=secrets.token_urlsafe(32), expires_at=payload.expires_at, download_limit=payload.download_limit, created_by_id=current_user.id, school_id=current_user.school_id)
        db.add(share)
        created.append(share)
    db.commit()
    for share in created:
        db.refresh(share)
    audit.record_audit(db, action="document.shared", current_user=current_user, entity_type="secure_file", entity_id=row.id, details={"shares": len(created), "share_type": payload.share_type, "mode": payload.mode})
    return created


@router.get("/{file_id}/shares", response_model=List[schemas.DocumentShareResponse])
def list_document_shares(file_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    row = _query_file(db, file_id, current_user)
    if row.uploaded_by_id != current_user.id and not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.DocumentShare).filter(models.DocumentShare.file_id == row.id).order_by(models.DocumentShare.created_at.desc()).all()


@router.post("/{file_id}/approve", response_model=schemas.SecureFileResponse)
def approve_file(file_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    row = _query_file(db, file_id, current_user)
    row.approval_status = "approved"
    row.approved_by_id = current_user.id
    row.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    audit.record_audit(db, action="document.approved", current_user=current_user, entity_type="secure_file", entity_id=row.id)
    return row


@router.post("/shares/{share_id}/revoke")
def revoke_share(share_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    share = db.query(models.DocumentShare).filter(models.DocumentShare.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    if share.created_by_id != current_user.id:
        # Admins may revoke shares only on files within their own school; the
        # platform Super Admin may revoke any. This prevents one school admin
        # from disrupting another school's document sharing.
        file_row = db.query(models.SecureFile).filter(models.SecureFile.id == share.file_id).first()
        same_school_admin = _is_admin(current_user) and file_row is not None and (
            current_user.role == models.UserRole.SUPER_ADMIN or file_row.school_id == current_user.school_id
        )
        if not same_school_admin:
            raise HTTPException(status_code=403, detail="Not authorized")
    share.status = "revoked"
    share.revoked_at = datetime.now(timezone.utc)
    db.commit()
    audit.record_audit(db, action="document.share.revoked", current_user=current_user, entity_type="document_share", entity_id=share.id)
    return {"message": "Share revoked"}


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    rbac.require_permission(current_user, "files:delete", db)
    row = _query_file(db, file_id, current_user)
    if row.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can delete this document")
    if row.entity_type == "generated" or row.uploaded_by_id is None:
        raise HTTPException(status_code=400, detail="Generated documents cannot be manually deleted")
    if db.query(models.DocumentShare).filter(models.DocumentShare.file_id == row.id, models.DocumentShare.status == "active").first():
        raise HTTPException(status_code=400, detail="Shared documents cannot be deleted until shares are revoked")
    row.status = "deleted"
    row.deleted_at = datetime.utcnow()
    db.commit()
    audit.record_audit(db, action="document.deleted", current_user=current_user, entity_type="secure_file", entity_id=row.id)
    return {"message": "File deleted"}
