"""Communication Platform — announcement center + emergency broadcast (Slice 4,
Loop 7 gap). Publishing fans the announcement out to recipients through the
existing notification infrastructure (`automation.record_notification`); the
external channel adapters (WhatsApp/voice/video) remain roadmap.
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security
from ..services import automation

router = APIRouter(prefix="/communication", tags=["Communication"])

PUBLISHER_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.TEACHER,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _ensure_publisher(current_user: models.User) -> None:
    if current_user.role not in PUBLISHER_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")


@router.get("/announcements", response_model=List[schemas.AnnouncementResponse])
def list_announcements(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return (
        db.query(models.Announcement)
        .filter(models.Announcement.school_id == _school_id(current_user))
        .order_by(models.Announcement.created_at.desc())
        .all()
    )


@router.post("/announcements", response_model=schemas.AnnouncementResponse)
def create_announcement(payload: schemas.AnnouncementCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_publisher(current_user)
    school_id = _school_id(current_user)
    status = "scheduled" if payload.scheduled_for else "draft"
    row = models.Announcement(
        **payload.model_dump(),
        school_id=school_id,
        status=status,
        created_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/announcements/{announcement_id}/publish", response_model=schemas.AnnouncementResponse)
def publish_announcement(announcement_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Publish now and fan out to the audience via the notification layer."""
    _ensure_publisher(current_user)
    school_id = _school_id(current_user)
    row = db.query(models.Announcement).filter(models.Announcement.id == announcement_id, models.Announcement.school_id == school_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Annonce introuvable")
    if row.status == "published":
        return row  # idempotent

    recipients = _audience_users(db, row)
    for user in recipients:
        automation.record_notification(
            db,
            event_type="announcement.emergency" if row.is_emergency else "announcement.published",
            subject=row.title,
            message=row.body,
            school_id=school_id,
            recipient_user=user,
            source_type="announcement",
            source_id=row.id,
            current_user=current_user,
        )
    row.status = "published"
    row.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def _audience_users(db: Session, announcement: models.Announcement) -> list[models.User]:
    query = db.query(models.User).filter(models.User.school_id == announcement.school_id, models.User.is_active == True)  # noqa: E712
    audience = announcement.audience
    if audience == "teachers":
        query = query.filter(models.User.role == models.UserRole.TEACHER)
    elif audience == "parents":
        query = query.filter(models.User.role == models.UserRole.PARENT)
    elif audience == "students":
        query = query.filter(models.User.role == models.UserRole.STUDENT)
    # "all" and "class" fall through to the whole school (class targeting refines
    # recipients once class membership lookup is wired; documented as a refinement).
    return query.limit(5000).all()
