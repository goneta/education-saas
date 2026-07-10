"""Diploma & certificate template engine.

Per-school templates (``DocumentTemplate``) with a dynamic ``{{placeholder}}``
engine resolved from REAL student/school data, rendered to a print-ready A4
landscape PDF by reportlab. Backgrounds: PNG/JPG are drawn as the full-page
background; PDF backgrounds are merged under the foreground with pypdf; DOCX
uploads are stored (downloadable) but rendered with the standard layout —
converting DOCX to PDF needs LibreOffice-class tooling we don't ship, and we
never fake. Every generated document is registered in ``DocumentRegistry``
(document_type = diploma | certificate) and stamped with the top-right
authenticity QR, so the public ``/verify/{uuid}`` page works for it.
"""

from __future__ import annotations

import io
import re
import uuid as _uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import models
from ..audit import record_audit
from . import document_registry

KINDS = ("diploma", "certificate")

# The supported dynamic fields (extensible: overrides may add new keys, and
# any {{key}} present in the resolved fields dict is substituted).
PLACEHOLDERS = [
    "student_name", "matricule", "school_name", "training_name", "course",
    "academic_year", "graduation_date", "certificate_number", "diploma_number",
    "director_name", "signature", "school_logo", "qr_code", "issue_date",
]

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

DEFAULT_TITLES = {"diploma": "DIPLÔME", "certificate": "CERTIFICAT"}
DEFAULT_BODIES = {
    "diploma": "Ce diplôme est décerné à {{student_name}} (matricule {{matricule}}) "
               "par {{school_name}} pour l'année académique {{academic_year}}, "
               "en reconnaissance de la réussite de {{training_name}}.",
    "certificate": "Ce certificat atteste que {{student_name}} (matricule {{matricule}}) "
                   "a suivi avec succès {{training_name}} au sein de {{school_name}} "
                   "durant l'année académique {{academic_year}}.",
}

SAMPLE_FIELDS = {
    "student_name": "Ada Lovelace",
    "matricule": "MAT-2026-00042",
    "training_name": "Baccalauréat série C",
    "course": "Terminale C",
    "graduation_date": "2026-07-08",
}


# --- CRUD helpers -------------------------------------------------------------

def list_templates(db: Session, school_id: int, *, kind: Optional[str] = None) -> list[models.DocumentTemplate]:
    q = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.school_id == school_id)
    if kind:
        q = q.filter(models.DocumentTemplate.kind == kind)
    return q.order_by(models.DocumentTemplate.is_default.desc(), models.DocumentTemplate.created_at.desc()).all()


def get_template(db: Session, school_id: int, template_id: int) -> Optional[models.DocumentTemplate]:
    return (
        db.query(models.DocumentTemplate)
        .filter(models.DocumentTemplate.id == template_id,
                models.DocumentTemplate.school_id == school_id)
        .first()
    )


def default_template(db: Session, school_id: int, kind: str) -> Optional[models.DocumentTemplate]:
    return (
        db.query(models.DocumentTemplate)
        .filter(models.DocumentTemplate.school_id == school_id,
                models.DocumentTemplate.kind == kind,
                models.DocumentTemplate.is_active.is_(True),
                models.DocumentTemplate.is_default.is_(True))
        .first()
    )


def create_template(db: Session, school_id: int, data: dict, user: models.User) -> models.DocumentTemplate:
    kind = data.get("kind") or "certificate"
    if kind not in KINDS:
        raise ValueError("invalid_kind")
    has_default = default_template(db, school_id, kind) is not None
    tpl = models.DocumentTemplate(
        school_id=school_id, kind=kind, name=data.get("name") or "Sans titre",
        description=data.get("description"),
        title_text=data.get("title_text"), body_text=data.get("body_text"),
        fields_config=data.get("fields_config"),
        is_default=bool(data.get("is_default")) or not has_default,
        is_active=True, created_by_id=user.id,
    )
    if tpl.is_default:
        _clear_default(db, school_id, kind)
        tpl.is_default = True
    db.add(tpl)
    db.flush()
    record_audit(db, action="document_template.created", current_user=user,
                 entity_type="document_template", entity_id=tpl.id, details={"kind": kind, "name": tpl.name})
    return tpl


def update_template(db: Session, tpl: models.DocumentTemplate, data: dict, user: models.User) -> models.DocumentTemplate:
    for field in ("name", "description", "title_text", "body_text", "fields_config", "is_active"):
        if field in data and data[field] is not None:
            setattr(tpl, field, data[field])
    if data.get("is_default"):
        _clear_default(db, tpl.school_id, tpl.kind)
        tpl.is_default = True
    record_audit(db, action="document_template.updated", current_user=user,
                 entity_type="document_template", entity_id=tpl.id, details={"name": tpl.name})
    db.flush()
    return tpl


def _clear_default(db: Session, school_id: int, kind: str) -> None:
    db.query(models.DocumentTemplate).filter(
        models.DocumentTemplate.school_id == school_id,
        models.DocumentTemplate.kind == kind,
    ).update({models.DocumentTemplate.is_default: False})


def set_default(db: Session, tpl: models.DocumentTemplate, user: models.User) -> models.DocumentTemplate:
    _clear_default(db, tpl.school_id, tpl.kind)
    tpl.is_default = True
    tpl.is_active = True
    record_audit(db, action="document_template.default", current_user=user,
                 entity_type="document_template", entity_id=tpl.id, details={"kind": tpl.kind})
    db.flush()
    return tpl


def duplicate_template(db: Session, tpl: models.DocumentTemplate, user: models.User) -> models.DocumentTemplate:
    copy = models.DocumentTemplate(
        school_id=tpl.school_id, kind=tpl.kind, name=f"{tpl.name} (copie)",
        description=tpl.description, title_text=tpl.title_text, body_text=tpl.body_text,
        background_path=tpl.background_path, background_type=tpl.background_type,
        background_filename=tpl.background_filename, fields_config=tpl.fields_config,
        is_default=False, is_active=True, created_by_id=user.id,
    )
    db.add(copy)
    db.flush()
    record_audit(db, action="document_template.duplicated", current_user=user,
                 entity_type="document_template", entity_id=copy.id, details={"from": tpl.id})
    return copy


def delete_template(db: Session, tpl: models.DocumentTemplate, user: models.User) -> None:
    record_audit(db, action="document_template.deleted", current_user=user,
                 entity_type="document_template", entity_id=tpl.id, details={"name": tpl.name})
    db.delete(tpl)
    db.flush()


# --- Field engine --------------------------------------------------------------

def resolve_fields(db: Session, school: models.School, profile: Optional[models.StudentProfile],
                   kind: str, overrides: Optional[dict] = None) -> dict:
    """Resolve every placeholder from REAL data; caller overrides win."""
    student_user = profile.user if profile else None
    class_name = None
    if profile and profile.current_class_id:
        cls = db.query(models.Class).filter(models.Class.id == profile.current_class_id).first()
        class_name = cls.name if cls else None
    year = (
        db.query(models.AcademicYear)
        .filter(models.AcademicYear.school_id == school.id, models.AcademicYear.is_current.is_(True))
        .first()
    )
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    number_prefix = "DIP" if kind == "diploma" else "CERT"
    number = f"{number_prefix}-{datetime.now(timezone.utc).year}-{_uuid.uuid4().hex[:8].upper()}"
    fields = {
        "student_name": (student_user.full_name if student_user else None) or "",
        "matricule": (profile.registration_number if profile else None) or "",
        "school_name": school.name or "",
        "training_name": "",
        "course": class_name or "",
        "academic_year": (year.name if year else None) or "",
        "graduation_date": today,
        "certificate_number": number if kind == "certificate" else "",
        "diploma_number": number if kind == "diploma" else "",
        "director_name": "",
        "signature": "",
        "school_logo": school.logo_url or "",
        "qr_code": "",  # rendered as an image, not text
        "issue_date": today,
    }
    for key, value in (overrides or {}).items():
        if value is not None:
            fields[str(key)] = str(value)
    return fields


def substitute(text: Optional[str], fields: dict) -> str:
    if not text:
        return ""
    return _PLACEHOLDER_RE.sub(lambda m: str(fields.get(m.group(1), "")), text)


# --- Renderer -------------------------------------------------------------------

def _wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    from reportlab.pdfbase.pdfmetrics import stringWidth

    lines: list[str] = []
    for paragraph in text.split("\n"):
        words, line = paragraph.split(), ""
        for word in words:
            trial = f"{line} {word}".strip()
            if stringWidth(trial, font, size) <= max_width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line)
    return lines


def render_pdf(tpl: Optional[models.DocumentTemplate], kind: str, fields: dict,
               qr_text: Optional[str], *, watermark: Optional[str] = None) -> bytes:
    """Render the document to a print-ready A4 landscape PDF."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as pdfcanvas

    page = landscape(A4)
    w, h = page
    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=page)

    background_pdf: Optional[bytes] = None
    bg_type = (tpl.background_type or "").lower() if tpl else ""
    if tpl and tpl.background_path and bg_type in {"png", "jpg", "jpeg"}:
        try:
            from . import file_storage
            path = file_storage.open_stored_file(tpl.background_path)
            c.drawImage(ImageReader(str(path)), 0, 0, width=w, height=h,
                        preserveAspectRatio=False, mask="auto")
        except Exception:
            pass  # fall through to the standard frame
    elif tpl and tpl.background_path and bg_type == "pdf":
        try:
            from . import file_storage
            background_pdf = file_storage.open_stored_file(tpl.background_path).read_bytes()
        except Exception:
            background_pdf = None

    if not (tpl and tpl.background_path and bg_type in {"png", "jpg", "jpeg"}) and not background_pdf:
        # Standard elegant frame (double border).
        c.setStrokeColorRGB(0.72, 0.58, 0.18)
        c.setLineWidth(3)
        c.rect(10 * mm, 10 * mm, w - 20 * mm, h - 20 * mm)
        c.setLineWidth(0.8)
        c.rect(13 * mm, 13 * mm, w - 26 * mm, h - 26 * mm)

    # Authenticity QR — top-right (spec position), clean margin.
    if qr_text:
        qr_size = 20 * mm
        try:
            document_registry.draw_qr_on_canvas(c, qr_text, w - 18 * mm - qr_size, h - 18 * mm - qr_size, qr_size)
            c.setFont("Helvetica", 5.5)
            c.setFillColorRGB(0.45, 0.45, 0.45)
            c.drawCentredString(w - 18 * mm - qr_size / 2, h - 20.5 * mm - qr_size, "Scan to verify")
        except Exception:
            pass  # QR must never break rendering

    # School name
    c.setFillColorRGB(0.15, 0.15, 0.15)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, h - 32 * mm, fields.get("school_name", ""))

    # Title
    title = substitute(tpl.title_text, fields) if (tpl and tpl.title_text) else DEFAULT_TITLES.get(kind, kind.upper())
    c.setFillColorRGB(0.55, 0.42, 0.05)
    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(w / 2, h - 55 * mm, title)

    # Student name
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(w / 2, h - 80 * mm, fields.get("student_name", ""))

    # Body paragraph (wrapped, centered)
    body = substitute(tpl.body_text, fields) if (tpl and tpl.body_text) else substitute(DEFAULT_BODIES.get(kind, ""), fields)
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.25, 0.25, 0.25)
    y = h - 97 * mm
    for line in _wrap(body, "Helvetica", 12, w - 90 * mm):
        c.drawCentredString(w / 2, y, line)
        y -= 6.5 * mm

    # Footer row: issue date (left) · number (center) · director/signature (right)
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(28 * mm, 30 * mm, f"Date : {fields.get('issue_date', '')}")
    number = fields.get("diploma_number") or fields.get("certificate_number") or ""
    if number:
        c.setFont("Helvetica", 8.5)
        c.drawCentredString(w / 2, 22 * mm, f"N° {number}")
    director = fields.get("director_name") or ""
    if director:
        c.setFont("Helvetica", 10)
        c.drawRightString(w - 28 * mm, 36 * mm, director)
        c.setLineWidth(0.6)
        c.setStrokeColorRGB(0.35, 0.35, 0.35)
        c.line(w - 75 * mm, 33 * mm, w - 28 * mm, 33 * mm)
        c.setFont("Helvetica", 8.5)
        c.drawRightString(w - 28 * mm, 29 * mm, fields.get("signature") or "Signature")

    if watermark:
        c.saveState()
        c.setFont("Helvetica-Bold", 60)
        c.setFillColorRGB(0.85, 0.85, 0.85)
        c.translate(w / 2, h / 2)
        c.rotate(25)
        c.drawCentredString(0, 0, watermark)
        c.restoreState()

    c.showPage()
    c.save()
    foreground = buf.getvalue()

    if background_pdf:
        try:
            import warnings
            warnings.filterwarnings("ignore")
            from pypdf import PdfReader, PdfWriter

            bg_reader = PdfReader(io.BytesIO(background_pdf))
            fg_reader = PdfReader(io.BytesIO(foreground))
            base = bg_reader.pages[0]
            base.merge_page(fg_reader.pages[0])
            writer = PdfWriter()
            writer.add_page(base)
            out = io.BytesIO()
            writer.write(out)
            return out.getvalue()
        except Exception:
            return foreground  # background merge must never block generation
    return foreground


# --- Generation (registry + QR) ---------------------------------------------------

def generate(db: Session, school: models.School, tpl: Optional[models.DocumentTemplate], kind: str,
             profile: models.StudentProfile, user: models.User,
             overrides: Optional[dict] = None) -> tuple[bytes, models.DocumentRegistry]:
    """Resolve fields from real data, register in DocumentRegistry, render the QR-stamped PDF."""
    fields = resolve_fields(db, school, profile, kind, overrides)
    number = fields.get("diploma_number") or fields.get("certificate_number") or ""
    payload = {
        "School Name": school.name,
        "Student Name": fields.get("student_name"),
        "Student ID": profile.id,
        "Matricule": fields.get("matricule"),
        "Academic Year": fields.get("academic_year"),
        "Date Generated": fields.get("issue_date"),
    }
    if kind == "diploma":
        payload.update({"Diploma Name": fields.get("training_name") or fields.get("course"),
                        "Graduation Date": fields.get("graduation_date"),
                        "Diploma Number": number})
    else:
        payload.update({"Training Name": fields.get("training_name") or fields.get("course"),
                        "Certificate Number": number})
    row = document_registry.register(
        db, document_type=kind, school_id=school.id,
        title=f"{DEFAULT_TITLES.get(kind, kind)} - {fields.get('student_name')}",
        reference=number, issued_to_name=fields.get("student_name"), issued_to_id=profile.id,
        payload=payload, issued_by=user,
    )
    record_audit(db, action=f"document_template.generated.{kind}", current_user=user,
                 entity_type="document_registry", entity_id=row.id,
                 details={"student_id": profile.id, "number": number, "template_id": tpl.id if tpl else None})
    pdf = render_pdf(tpl, kind, fields, document_registry.qr_text(row))
    return pdf, row
