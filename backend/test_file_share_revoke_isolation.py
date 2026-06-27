import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import files


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _admin(db, school):
    user = models.User(email=f"admin-{uuid.uuid4().hex[:6]}@test.local", hashed_password="x", full_name="A", role=models.UserRole.SCHOOL_ADMIN, school=school, is_active=True)
    db.add(user)
    db.flush()
    return user


def _fixtures(db):
    school_a = models.School(name="A", domain_prefix=f"a{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL)
    school_b = models.School(name="B", domain_prefix=f"b{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL)
    db.add_all([school_a, school_b])
    db.flush()
    admin_a = _admin(db, school_a)
    admin_b = _admin(db, school_b)
    secure_file = models.SecureFile(
        original_filename="doc.pdf", stored_filename=uuid.uuid4().hex, content_type="application/pdf",
        size_bytes=10, checksum_sha256="abc", storage_path="/x", school_id=school_a.id, uploaded_by_id=admin_a.id,
    )
    db.add(secure_file)
    db.flush()
    share = models.DocumentShare(
        file_id=secure_file.id, share_type="B2P", mode="private", status="active",
        encrypted_token=uuid.uuid4().hex, created_by_id=admin_a.id,
    )
    db.add(share)
    db.commit()
    return admin_a, admin_b, share


def test_other_school_admin_cannot_revoke_share():
    db = _session()
    _admin_a, admin_b, share = _fixtures(db)
    with pytest.raises(HTTPException) as exc:
        files.revoke_share(share_id=share.id, current_user=admin_b, db=db)
    assert exc.value.status_code == 403
    db.refresh(share)
    assert share.status == "active"  # untouched


def test_owning_school_admin_can_revoke_share():
    db = _session()
    admin_a, _admin_b, share = _fixtures(db)
    result = files.revoke_share(share_id=share.id, current_user=admin_a, db=db)
    assert "revoked" in result["message"].lower()
    db.refresh(share)
    assert share.status == "revoked"
