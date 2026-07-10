import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import document_templates as R
from backend.routers import verify as VR
from backend.services import document_templates as svc


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school(db):
    tag = uuid.uuid4().hex[:6]
    s = models.School(name=f"Lycee {tag}", domain_prefix=f"s_{tag}", school_type=models.SchoolType.GENERAL)
    db.add(s); db.commit()
    return s


def _admin(db, school, role=models.UserRole.SCHOOL_ADMIN):
    tag = uuid.uuid4().hex[:5]
    u = models.User(email=f"a_{tag}@x.com", hashed_password="x", full_name="Admin", role=role,
                    school_id=school.id, is_active=True)
    db.add(u); db.commit()
    return u


def _student(db, school, with_class=True, with_year=True):
    tag = uuid.uuid4().hex[:5]
    cls = None
    if with_class:
        cls = models.Class(name=f"Terminale C {tag}", school_id=school.id)
        db.add(cls); db.flush()
    if with_year:
        db.add(models.AcademicYear(name="2025-2026", school_id=school.id, is_current=True))
    u = models.User(email=f"s_{tag}@x.com", hashed_password="x", full_name=f"Eleve {tag}",
                    role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(u); db.flush()
    p = models.StudentProfile(user_id=u.id, registration_number=f"MAT-{tag}",
                              current_class_id=cls.id if cls else None)
    db.add(p); db.commit()
    return u, p


def test_crud_default_duplicate_and_rbac():
    db = _session()
    school = _school(db)
    admin = _admin(db, school)

    # First template of a kind becomes default automatically.
    t1 = R.create_template(schemas.DocumentTemplateCreate(kind="diploma", name="Classique"),
                           school_id=None, db=db, current_user=admin)
    assert t1.is_default is True

    t2 = R.create_template(schemas.DocumentTemplateCreate(kind="diploma", name="Moderne"),
                           school_id=None, db=db, current_user=admin)
    assert t2.is_default is False

    # set_default switches the flag exclusively.
    R.set_default_template(t2.id, school_id=None, db=db, current_user=admin)
    rows = R.list_templates(kind="diploma", school_id=None, db=db, current_user=admin)
    flags = {r.id: r.is_default for r in rows}
    assert flags[t2.id] is True and flags[t1.id] is False

    # Duplicate copies content but never the default flag.
    copy = R.duplicate_template(t2.id, school_id=None, db=db, current_user=admin)
    assert copy.name.endswith("(copie)") and copy.is_default is False

    # Update + deactivate.
    upd = R.update_template(t1.id, schemas.DocumentTemplateUpdate(name="Classique v2", is_active=False),
                            school_id=None, db=db, current_user=admin)
    assert upd.name == "Classique v2" and upd.is_active is False

    # Delete.
    R.delete_template(copy.id, school_id=None, db=db, current_user=admin)
    assert svc.get_template(db, school.id, copy.id) is None

    # Invalid kind -> 422; teacher -> 403; cross-school -> 404.
    with pytest.raises(HTTPException) as e1:
        R.create_template(schemas.DocumentTemplateCreate(kind="badge", name="X"),
                          school_id=None, db=db, current_user=admin)
    assert e1.value.status_code == 422
    teacher = _admin(db, school, role=models.UserRole.TEACHER)
    with pytest.raises(HTTPException) as e2:
        R.list_templates(kind=None, school_id=None, db=db, current_user=teacher)
    assert e2.value.status_code == 403
    other = _school(db)
    other_admin = _admin(db, other)
    with pytest.raises(HTTPException) as e3:
        R.update_template(t1.id, schemas.DocumentTemplateUpdate(name="Vol"),
                          school_id=None, db=db, current_user=other_admin)
    assert e3.value.status_code == 404


def test_field_engine_resolves_real_data_and_overrides():
    db = _session()
    school = _school(db)
    _, profile = _student(db, school)

    fields = svc.resolve_fields(db, school, profile, "diploma", {"training_name": "Bac C", "director_name": "M. Kone"})
    assert fields["student_name"].startswith("Eleve ")
    assert fields["matricule"].startswith("MAT-")
    assert fields["school_name"] == school.name
    assert fields["course"].startswith("Terminale C")
    assert fields["academic_year"] == "2025-2026"
    assert fields["diploma_number"].startswith("DIP-") and fields["certificate_number"] == ""
    assert fields["training_name"] == "Bac C" and fields["director_name"] == "M. Kone"

    text = svc.substitute("{{student_name}} - {{unknown_key}} - {{ matricule }}", fields)
    assert fields["student_name"] in text and fields["matricule"] in text
    assert "unknown_key" not in text and "{{" not in text


def test_generate_registers_and_pdf_is_verifiable():
    db = _session()
    school = _school(db)
    admin = _admin(db, school)
    _, profile = _student(db, school)
    tpl = R.create_template(schemas.DocumentTemplateCreate(
        kind="certificate", name="Std",
        body_text="Certifie que {{student_name}} ({{matricule}}) a suivi {{training_name}}."),
        school_id=None, db=db, current_user=admin)

    resp = R.generate_document(schemas.DocumentGenerateRequest(
        student_id=profile.id, kind="certificate", overrides={"training_name": "Formation Python"}),
        school_id=None, db=db, current_user=admin)
    assert resp.media_type == "application/pdf" and resp.body[:4] == b"%PDF"
    assert "certificate-CERT-" in resp.headers["Content-Disposition"]

    row = db.query(models.DocumentRegistry).filter(
        models.DocumentRegistry.document_type == "certificate").first()
    assert row is not None and row.school_id == school.id
    assert row.payload["Training Name"] == "Formation Python"
    assert row.payload["Matricule"].startswith("MAT-")
    assert row.reference.startswith("CERT-")

    v = VR.verify_document(row.uuid, db=db)
    assert v["valid"] is True and v["document_type"] == "certificate"
    assert v["school_name"] == school.name

    # Default template resolution: template_id omitted uses the school default (tpl).
    resp2 = R.generate_document(schemas.DocumentGenerateRequest(student_id=profile.id, kind="diploma"),
                                school_id=None, db=db, current_user=admin)
    assert resp2.body[:4] == b"%PDF"
    assert db.query(models.DocumentRegistry).filter(
        models.DocumentRegistry.document_type == "diploma").count() == 1
    _ = tpl

    # Unknown student -> 404; missing kind and template -> 422.
    with pytest.raises(HTTPException) as e1:
        R.generate_document(schemas.DocumentGenerateRequest(student_id=999999, kind="diploma"),
                            school_id=None, db=db, current_user=admin)
    assert e1.value.status_code == 404
    with pytest.raises(HTTPException) as e2:
        R.generate_document(schemas.DocumentGenerateRequest(student_id=profile.id),
                            school_id=None, db=db, current_user=admin)
    assert e2.value.status_code == 422


def test_preview_watermarked_and_not_registered():
    db = _session()
    school = _school(db)
    admin = _admin(db, school)
    tpl = R.create_template(schemas.DocumentTemplateCreate(kind="diploma", name="Std"),
                            school_id=None, db=db, current_user=admin)
    resp = R.preview_template(tpl.id, schemas.DocumentPreviewRequest(), school_id=None,
                              db=db, current_user=admin)
    assert resp.media_type == "application/pdf" and resp.body[:4] == b"%PDF"
    # Preview never touches the registry.
    assert db.query(models.DocumentRegistry).count() == 0


def test_placeholders_listed():
    db = _session()
    school = _school(db)
    admin = _admin(db, school)
    out = R.list_placeholders(current_user=admin)
    assert "student_name" in out["placeholders"] and "qr_code" in out["placeholders"]
    _ = db, school
