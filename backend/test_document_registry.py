import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import billing as BR
from backend.routers import verify as VR
from backend.services import billing as bsvc
from backend.services import document_registry as dr


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"S {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL,
                      default_currency="FCFA")
    db.add(s); db.commit()
    return s


def _admin(db, school):
    tag = uuid.uuid4().hex[:5]
    u = models.User(email=f"a_{tag}@x.com", hashed_password="x", full_name="Admin",
                    role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    db.add(u); db.commit()
    return u


def test_register_is_idempotent_per_source_and_hashes():
    db = _session()
    school = _school(db)
    admin = _admin(db, school)
    r1 = dr.register(db, document_type="invoice", school_id=school.id, title="Invoice A",
                     reference="INV-A", payload={"a": 1}, source_type="invoice", source_id=42, issued_by=admin)
    db.commit()
    assert r1.uuid and r1.content_hash == dr.content_hash({"a": 1})
    # Same source -> same row (updated), not a duplicate.
    r2 = dr.register(db, document_type="invoice", school_id=school.id, title="Invoice A2",
                     reference="INV-A", payload={"a": 2}, source_type="invoice", source_id=42)
    db.commit()
    assert r2.id == r1.id and r2.uuid == r1.uuid
    assert r2.title == "Invoice A2" and r2.content_hash == dr.content_hash({"a": 2})
    assert db.query(models.DocumentRegistry).count() == 1


def test_qr_data_and_png():
    db = _session()
    school = _school(db)
    row = dr.register(db, document_type="diploma", school_id=school.id, payload={"Student Name": "Ada"},
                      source_type="diploma", source_id=7)
    db.commit()
    data = dr.qr_data(row)
    assert data["type"] == "diploma" and data["uuid"] == row.uuid
    assert data["verify_url"].endswith(f"/verify/{row.uuid}")
    assert data["Student Name"] == "Ada"
    png = dr.render_qr_png(dr.qr_text(row))
    assert png[:4] == b"\x89PNG"


def test_verify_valid_notfound_and_revoke():
    db = _session()
    school = _school(db)
    admin = _admin(db, school)
    row = dr.register(db, document_type="certificate", school_id=school.id, title="Cert",
                      issued_to_name="Bob", payload={"School Name": school.name},
                      source_type="certificate", source_id=1)
    db.commit()

    v = VR.verify_document(row.uuid, db=db)
    assert v["valid"] is True and v["status"] == "valid"
    assert v["school_name"] == school.name and v["issued_to"] == "Bob"
    assert v["verify_url"].endswith(row.uuid)

    assert VR.verify_document("does-not-exist", db=db) == {"valid": False, "status": "not_found"}

    dr.revoke(db, row.uuid, admin); db.commit()
    v2 = VR.verify_document(row.uuid, db=db)
    assert v2["valid"] is False and v2["status"] == "revoked"


def test_invoice_pdf_embeds_registry_qr_and_is_verifiable():
    db = _session()
    school = _school(db)
    admin = _admin(db, school)
    pay = models.PlatformPayment(reference="SUB-QR", school_id=school.id, payment_type="subscription",
                                 amount=99000, currency="FCFA", provider="stripe", status="successful",
                                 beneficiary_entity="platform", metadata_json={"plan": "pro"})
    db.add(pay); db.commit()

    # Router path: detail + registry + commit.
    detail = BR.get_invoice_detail(pay.id, school_id=None, db=db, current_user=admin)
    assert detail["uuid"] and detail["verify_url"].endswith(detail["uuid"])
    assert "Invoice Number" in detail["qr_text"]

    # A registry row now exists and is verifiable.
    row = db.query(models.DocumentRegistry).filter(models.DocumentRegistry.source_type == "invoice",
                                                   models.DocumentRegistry.source_id == pay.id).first()
    assert row is not None and row.document_type == "invoice"
    assert VR.verify_document(row.uuid, db=db)["valid"] is True

    # The PDF renders with the QR (real %PDF).
    pdf = bsvc.render_invoice_pdf(detail)
    assert pdf[:4] == b"%PDF"

    # Regenerating does not create a duplicate registry row (idempotent).
    BR.get_invoice_pdf(pay.id, school_id=None, db=db, current_user=admin)
    assert db.query(models.DocumentRegistry).filter(models.DocumentRegistry.source_id == pay.id).count() == 1
