"""Public partner REST API (v1) — third-party, server-to-server access.

Authentication is a tenant **API key** sent as `X-API-Key` (minted and revoked
in `/extensibility/api-keys`; only the SHA-256 hash is stored). Every request is
scoped to the key's school — a partner can never read another tenant's data.
Endpoints are read-only, paginated (`limit` ≤ 200, `offset`), and described in
the OpenAPI schema like every other router.

Outbound side: modules publish platform events through
`extensibility.emit_event`, which queues signed deliveries per subscribed
webhook endpoint (see `/extensibility/webhooks`).
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

import hashlib

from .. import database, models
from ..schemas import (
    PublicClass, PublicStudent, PublicTeacher, PublicSubject, PublicAnnouncement, PublicKeyInfo,
)

router = APIRouter(prefix="/api/v1", tags=["Public API (v1)"])

MAX_LIMIT = 200


def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(database.get_db),
) -> models.ApiKey:
    """Resolve and validate the partner API key; returns the ApiKey row (which
    carries the tenant scope). 401 on missing/unknown/revoked keys."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    row = db.query(models.ApiKey).filter(
        models.ApiKey.key_hash == key_hash,
        models.ApiKey.is_active == True,  # noqa: E712
    ).first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    row.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return row


def _page(limit: int, offset: int) -> tuple[int, int]:
    return min(max(limit, 1), MAX_LIMIT), max(offset, 0)


@router.get("/me", response_model=PublicKeyInfo)
def key_info(api_key: models.ApiKey = Depends(require_api_key), db: Session = Depends(database.get_db)):
    """Identify the calling key and its tenant scope."""
    school = db.query(models.School).filter(models.School.id == api_key.school_id).first()
    return PublicKeyInfo(key_name=api_key.name, key_prefix=api_key.prefix, school_id=api_key.school_id, school_name=school.name if school else None)


@router.get("/students", response_model=List[PublicStudent])
def list_students(limit: int = Query(50), offset: int = Query(0), api_key: models.ApiKey = Depends(require_api_key), db: Session = Depends(database.get_db)):
    limit, offset = _page(limit, offset)
    rows = (
        db.query(models.User, models.StudentProfile)
        .join(models.StudentProfile, models.StudentProfile.user_id == models.User.id)
        .filter(models.User.school_id == api_key.school_id, models.User.role.in_([models.UserRole.STUDENT, models.UserRole.PUPIL]))
        .order_by(models.User.id.asc())
        .offset(offset).limit(limit).all()
    )
    class_names = {c.id: c.name for c in db.query(models.Class).filter(models.Class.school_id == api_key.school_id).all()}
    return [
        PublicStudent(
            id=user.id, full_name=user.full_name, email=user.email, is_active=bool(user.is_active),
            registration_number=profile.registration_number, gender=profile.gender,
            class_id=profile.current_class_id, class_name=class_names.get(profile.current_class_id),
        )
        for user, profile in rows
    ]


@router.get("/teachers", response_model=List[PublicTeacher])
def list_teachers(limit: int = Query(50), offset: int = Query(0), api_key: models.ApiKey = Depends(require_api_key), db: Session = Depends(database.get_db)):
    limit, offset = _page(limit, offset)
    rows = (
        db.query(models.User)
        .filter(models.User.school_id == api_key.school_id, models.User.role.in_([models.UserRole.TEACHER, models.UserRole.TRAINER, models.UserRole.INSTRUCTOR]))
        .order_by(models.User.id.asc())
        .offset(offset).limit(limit).all()
    )
    return [PublicTeacher(id=u.id, full_name=u.full_name, email=u.email, is_active=bool(u.is_active)) for u in rows]


@router.get("/classes", response_model=List[PublicClass])
def list_classes(limit: int = Query(100), offset: int = Query(0), api_key: models.ApiKey = Depends(require_api_key), db: Session = Depends(database.get_db)):
    limit, offset = _page(limit, offset)
    rows = (
        db.query(models.Class)
        .filter(models.Class.school_id == api_key.school_id)
        .order_by(models.Class.name.asc())
        .offset(offset).limit(limit).all()
    )
    return [PublicClass(id=c.id, name=c.name, level=c.level) for c in rows]


@router.get("/subjects", response_model=List[PublicSubject])
def list_subjects(limit: int = Query(100), offset: int = Query(0), api_key: models.ApiKey = Depends(require_api_key), db: Session = Depends(database.get_db)):
    limit, offset = _page(limit, offset)
    rows = (
        db.query(models.Subject)
        .filter(models.Subject.school_id == api_key.school_id)
        .order_by(models.Subject.name.asc())
        .offset(offset).limit(limit).all()
    )
    return [PublicSubject(id=s.id, name=s.name, coefficient=s.coefficient) for s in rows]


@router.get("/announcements", response_model=List[PublicAnnouncement])
def list_announcements(limit: int = Query(50), offset: int = Query(0), api_key: models.ApiKey = Depends(require_api_key), db: Session = Depends(database.get_db)):
    """Published announcements only — the outward-facing communication feed."""
    limit, offset = _page(limit, offset)
    rows = (
        db.query(models.Announcement)
        .filter(models.Announcement.school_id == api_key.school_id, models.Announcement.status == "published")
        .order_by(models.Announcement.id.desc())
        .offset(offset).limit(limit).all()
    )
    return [
        PublicAnnouncement(id=a.id, title=a.title, body=a.body, audience=a.audience, is_emergency=bool(a.is_emergency), published_at=a.published_at)
        for a in rows
    ]
