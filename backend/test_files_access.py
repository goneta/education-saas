"""Lot 5 — audit QUAL-01 : le contrôle d'accès aux fichiers n'avait aucun test.

`routers/files.py` decides who may read every uploaded document (student files,
payslips, medical scans…). It was one of the least-tested modules of the whole
backend while being one of the most damaging to get wrong.
"""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers.files import _can_access_file


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(s); db.commit()
    return s


def _user(db, school, role=models.UserRole.TEACHER):
    tag = uuid.uuid4().hex[:6]
    u = models.User(email=f"u_{tag}@x.com", hashed_password="x", full_name="U", role=role,
                    school_id=school.id if school else None, is_active=True)
    db.add(u); db.commit()
    return u


def _file(db, school, owner, *, visibility="private", approval_status="approved"):
    tag = uuid.uuid4().hex[:8]
    row = models.SecureFile(
        original_filename=f"doc-{tag}.pdf",
        stored_filename=f"{tag}.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        checksum_sha256=tag * 8,
        storage_path=f"/tmp/{tag}",
        school_id=school.id if school else None,
        uploaded_by_id=owner.id if owner else None,
        visibility=visibility,
        approval_status=approval_status,
    )
    db.add(row); db.commit()
    return row


def test_owner_and_school_admin_can_read_a_private_file():
    db = _session()
    school = _school(db)
    owner = _user(db, school)
    admin = _user(db, school, models.UserRole.SCHOOL_ADMIN)
    row = _file(db, school, owner)

    assert _can_access_file(db, row, owner) is True
    assert _can_access_file(db, row, admin) is True


def test_another_school_can_never_read_the_file():
    """The finding that matters: cross-tenant document access."""
    db = _session()
    school_a, school_b = _school(db), _school(db)
    owner = _user(db, school_a)
    row = _file(db, school_a, owner)

    outsider = _user(db, school_b)
    outsider_admin = _user(db, school_b, models.UserRole.SCHOOL_ADMIN)
    assert _can_access_file(db, row, outsider) is False
    assert _can_access_file(db, row, outsider_admin) is False


def test_colleague_needs_an_explicit_share_or_public_visibility():
    db = _session()
    school = _school(db)
    owner = _user(db, school)
    colleague = _user(db, school)
    row = _file(db, school, owner)

    # Same school is NOT enough for a private document.
    assert _can_access_file(db, row, colleague) is False

    # An explicit share opens it.
    db.add(models.DocumentShare(file_id=row.id, recipient_user_id=colleague.id,
                                share_type="user", status="active", school_id=school.id,
                                encrypted_token=uuid.uuid4().hex, created_by_id=owner.id))
    db.commit()
    assert _can_access_file(db, row, colleague) is True

    # Internal visibility opens it school-wide once approved.
    other = _user(db, school)
    internal = _file(db, school, owner, visibility="public_internal", approval_status="approved")
    assert _can_access_file(db, internal, other) is True
    pending = _file(db, school, owner, visibility="public_internal", approval_status="pending")
    assert _can_access_file(db, pending, other) is False


def test_super_admin_can_read_any_school_file():
    db = _session()
    school = _school(db)
    owner = _user(db, school)
    row = _file(db, school, owner)
    super_admin = _user(db, None, models.UserRole.SUPER_ADMIN)
    assert _can_access_file(db, row, super_admin) is True
