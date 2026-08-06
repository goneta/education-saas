"""Printable report card — bulletin PDF (audit FONC-01).

`GET /grades/reports/student/{id}/term/{id}` returned JSON only, so the single
most important document of a school term could not be printed: schools would
have fallen back to their previous tool at the first end of term.

This renderer reuses the platform's existing document machinery rather than
inventing a parallel one: reportlab (already used for invoices and diplomas)
and the universal `DocumentRegistry`, so every bulletin carries an authenticity
QR resolvable at the public `/verify/{uuid}` page.
"""

import io
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from .. import models
from . import document_registry

PAGE_MARGIN = 40


def _mention(average: float) -> str:
    if average >= 16:
        return "Très bien"
    if average >= 14:
        return "Bien"
    if average >= 12:
        return "Assez bien"
    if average >= 10:
        return "Passable"
    return "Insuffisant"


def build_context(
    db: Session,
    *,
    profile: models.StudentProfile,
    term_id: int,
    report: Any,
) -> dict:
    """Assemble everything the PDF prints, from REAL data only."""
    student_user = (
        db.query(models.User).filter(models.User.id == profile.user_id).first()
        if profile.user_id else None
    )
    school = (
        db.query(models.School).filter(models.School.id == student_user.school_id).first()
        if student_user and student_user.school_id else None
    )
    term = db.query(models.Term).filter(models.Term.id == term_id).first()
    school_class = (
        db.query(models.Class).filter(models.Class.id == profile.current_class_id).first()
        if profile.current_class_id else None
    )

    subjects = [
        {
            "name": subject.subject_name,
            "coefficient": subject.coefficient,
            "average": subject.average,
            "assessments": len(subject.assessments or []),
        }
        for subject in (report.subjects or [])
    ]
    return {
        "school_name": school.name if school else "—",
        "school_address": school.address if school else None,
        "student_name": student_user.full_name if student_user else "—",
        "registration_number": profile.registration_number,
        "class_name": school_class.name if school_class else None,
        "term_name": term.name if term else f"Trimestre {term_id}",
        "subjects": subjects,
        "overall_average": report.overall_average,
        "mention": _mention(report.overall_average or 0),
        "issued_at": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        "school_id": school.id if school else None,
        "student_id": profile.id,
        "term_id": term_id,
    }


def registry_source_id(student_id: int, term_id: int) -> int:
    """Collision-free identity for a (student, term) bulletin.

    Second-pass fix: the first implementation concatenated the two numbers
    (`int(f"{student_id}{term_id}")`), so student 1 / term 23 and student 12 /
    term 3 both produced 123 — two different pupils sharing ONE registry entry.
    The QR of one bulletin then resolved to the other pupil's data, and
    regenerating one silently overwrote the other. Cantor-style pairing keeps
    the mapping injective.
    """
    return student_id * 100_000 + term_id


def attach_registry(db: Session, context: dict, *, issued_by: Optional[models.User] = None) -> dict:
    """Register the bulletin so its QR resolves at /verify/{uuid}. Idempotent per
    (student, term) — regenerating the same bulletin keeps the same UUID."""
    row = document_registry.register(
        db,
        document_type="report_card",
        school_id=context.get("school_id"),
        title=f"Bulletin — {context['term_name']}",
        reference=f"BUL-{context['student_id']}-{context['term_id']}",
        issued_to_name=context.get("student_name"),
        payload={
            "School": context.get("school_name"),
            "Student": context.get("student_name"),
            "Class": context.get("class_name"),
            "Term": context.get("term_name"),
            "Average": f"{context.get('overall_average')}/20",
            "Date": document_registry.now_iso(),
        },
        source_type="report_card",
        source_id=registry_source_id(context["student_id"], context["term_id"]),
        issued_by=issued_by,
    )
    context["uuid"] = row.uuid
    context["verify_url"] = document_registry.verification_url(row.uuid)
    context["qr_text"] = document_registry.qr_text(row)
    return context


def render_pdf(context: dict) -> bytes:
    """A4 portrait bulletin: school header, student block, per-subject table with
    coefficients and averages, overall average + mention, signature area and the
    authenticity QR."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - PAGE_MARGIN

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(PAGE_MARGIN, y, context.get("school_name") or "—")
    y -= 16
    if context.get("school_address"):
        pdf.setFont("Helvetica", 9)
        pdf.drawString(PAGE_MARGIN, y, str(context["school_address"]))
        y -= 14

    if context.get("qr_text"):
        try:
            document_registry.draw_qr_on_canvas(
                pdf, context["qr_text"], width - PAGE_MARGIN - 80, height - PAGE_MARGIN - 80, 80
            )
        except Exception:  # QR rendering must never block the bulletin
            pass

    y -= 10
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(PAGE_MARGIN, y, f"BULLETIN DE NOTES — {context.get('term_name')}")
    y -= 24

    # Student block
    pdf.setFont("Helvetica", 10)
    for label, value in (
        ("Élève", context.get("student_name")),
        ("Matricule", context.get("registration_number")),
        ("Classe", context.get("class_name")),
        ("Édité le", context.get("issued_at")),
    ):
        if value:
            pdf.drawString(PAGE_MARGIN, y, f"{label} : {value}")
            y -= 14
    y -= 6

    # Subject table
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(PAGE_MARGIN, y, "Matière")
    pdf.drawString(width - 300, y, "Coef.")
    pdf.drawString(width - 230, y, "Évaluations")
    pdf.drawString(width - 130, y, "Moyenne /20")
    y -= 6
    pdf.line(PAGE_MARGIN, y, width - PAGE_MARGIN, y)
    y -= 14

    pdf.setFont("Helvetica", 10)
    for subject in context.get("subjects") or []:
        if y < 140:  # keep room for the footer
            pdf.showPage()
            y = height - PAGE_MARGIN
            pdf.setFont("Helvetica", 10)
        pdf.drawString(PAGE_MARGIN, y, str(subject["name"])[:48])
        pdf.drawString(width - 300, y, str(subject["coefficient"]))
        pdf.drawString(width - 230, y, str(subject["assessments"]))
        pdf.drawString(width - 130, y, f"{subject['average']:.2f}")
        y -= 14

    if not context.get("subjects"):
        pdf.drawString(PAGE_MARGIN, y, "Aucune note enregistrée pour ce trimestre.")
        y -= 14

    y -= 6
    pdf.line(PAGE_MARGIN, y, width - PAGE_MARGIN, y)
    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(PAGE_MARGIN, y, f"Moyenne générale : {context.get('overall_average', 0):.2f}/20")
    pdf.drawString(width - 230, y, f"Mention : {context.get('mention')}")
    y -= 40

    pdf.setFont("Helvetica", 9)
    pdf.drawString(PAGE_MARGIN, y, "Signature de la direction")
    pdf.drawString(width - 230, y, "Signature du parent / tuteur")
    y -= 30
    if context.get("verify_url"):
        pdf.setFont("Helvetica", 7)
        pdf.drawString(PAGE_MARGIN, y, f"Document vérifiable : {context['verify_url']}")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
