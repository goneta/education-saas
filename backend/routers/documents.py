from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import audit, database, models, pdf, rbac, security

router = APIRouter(prefix="/documents", tags=["Documents"])


def _student(db: Session, student_user_id: int, current_user: models.User) -> models.User:
    student = db.query(models.User).filter(models.User.id == student_user_id, models.User.role == models.UserRole.STUDENT).first()
    if not student or not student.student_profile:
        raise HTTPException(status_code=404, detail="Student not found")
    if current_user.school_id and student.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Student belongs to another school")
    return student


def _require_code(expected: str | None, provided: str | None) -> None:
    if not expected or not provided or provided != expected:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/verify/{document_type}/{document_id}")
def verify_document(document_type: str, document_id: int, code: str | None = Query(default=None), db: Session = Depends(database.get_db)):
    if document_type == "receipt":
        payment = db.query(models.Payment).filter(models.Payment.id == document_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Document not found")
        _require_code(payment.receipt_number, code)
        return {"valid": True, "document_type": document_type, "document_id": document_id, "reference": payment.receipt_number, "issued_at": payment.payment_date}
    if document_type == "certificate":
        cert = db.query(models.CertificateRequest).filter(models.CertificateRequest.id == document_id).first()
        if not cert:
            raise HTTPException(status_code=404, detail="Document not found")
        _require_code(f"CERT-{cert.id}", code)
        return {"valid": cert.status != models.CertificateStatus.BLOCKED, "document_type": document_type, "document_id": document_id, "reference": f"CERT-{cert.id}", "issued_at": cert.generated_at}
    if document_type == "diploma":
        diploma = db.query(models.DiplomaRecord).filter(models.DiplomaRecord.id == document_id).first()
        if not diploma:
            raise HTTPException(status_code=404, detail="Document not found")
        _require_code(diploma.certificate_number, code)
        return {"valid": diploma.is_certified, "document_type": document_type, "document_id": document_id, "reference": diploma.certificate_number, "issued_at": diploma.issued_date}
    raise HTTPException(status_code=404, detail="Unsupported document type")


@router.get("/students/{student_user_id}/receipt/{payment_id}.pdf")
def payment_receipt_pdf(student_user_id: int, payment_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    rbac.require_permission(current_user, "documents:receipt")
    student = _student(db, student_user_id, current_user)
    payment = db.query(models.Payment).join(models.Fee).filter(models.Payment.id == payment_id, models.Fee.student_id == student.student_profile.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    generated = db.query(models.GeneratedDocument).filter(
        models.GeneratedDocument.source_type == "payment",
        models.GeneratedDocument.source_id == payment.id,
        models.GeneratedDocument.document_type == models.GeneratedDocumentType.RECEIPT,
    ).first()
    if generated:
        generated.downloaded_at = __import__("datetime").datetime.utcnow()
        audit.record_audit(db, action="automation.document.downloaded", current_user=current_user, entity_type="generated_document", entity_id=generated.id, details={"type": "receipt"})
        db.commit()
    lines = [
        f"Student: {student.full_name}",
        f"Matricule: {student.student_profile.registration_number}",
        f"Fee: {payment.fee.title}",
        f"Receipt: {payment.receipt_number}",
        f"Amount: {payment.amount:,.0f} {student.school.default_currency if student.school else 'FCFA'}",
        f"Date: {payment.payment_date}",
        f"Operator: {payment.recorded_by.full_name if payment.recorded_by else '-'}",
        f"Locale: {student.school.primary_language if student.school else 'fr'} / {student.school.timezone if student.school else 'Africa/Abidjan'}",
        f"Verification: /documents/verify/receipt/{payment.id}?code={payment.receipt_number}",
        f"QR payload: VERIFY:receipt:{payment.id}:{payment.receipt_number}",
    ]
    return Response(pdf.professional_pdf("Recu de paiement", lines, f"/documents/verify/receipt/{payment.id}?code={payment.receipt_number}"), media_type="application/pdf")


@router.get("/students/{student_user_id}/certificate/{certificate_id}.pdf")
def certificate_pdf(student_user_id: int, certificate_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    rbac.require_permission(current_user, "documents:issue")
    student = _student(db, student_user_id, current_user)
    cert = db.query(models.CertificateRequest).filter(models.CertificateRequest.id == certificate_id, models.CertificateRequest.student_id == student.student_profile.id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.status == models.CertificateStatus.BLOCKED:
        raise HTTPException(status_code=400, detail=cert.blocked_reason or "Certificate is blocked")
    generated = db.query(models.GeneratedDocument).filter(
        models.GeneratedDocument.source_type == "certificate",
        models.GeneratedDocument.source_id == cert.id,
        models.GeneratedDocument.document_type == models.GeneratedDocumentType.CERTIFICATE,
    ).first()
    if generated:
        generated.downloaded_at = __import__("datetime").datetime.utcnow()
        audit.record_audit(db, action="automation.document.downloaded", current_user=current_user, entity_type="generated_document", entity_id=generated.id, details={"type": "certificate"})
        db.commit()
    lines = [
        f"Student: {student.full_name}",
        f"Matricule: {student.student_profile.registration_number}",
        f"Type: {cert.certificate_type.value}",
        f"Country: {student.school.country_code if student.school else '-'}",
        cert.content or "Certificate generated by school administration.",
        f"Generated at: {cert.generated_at}",
        f"Verification: /documents/verify/certificate/{cert.id}?code=CERT-{cert.id}",
        f"QR payload: VERIFY:certificate:{cert.id}:CERT-{cert.id}",
    ]
    return Response(pdf.professional_pdf("Attestation", lines, f"/documents/verify/certificate/{cert.id}?code=CERT-{cert.id}"), media_type="application/pdf")


@router.get("/students/{student_user_id}/report-card.pdf")
def report_card_pdf(student_user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    rbac.require_permission(current_user, "reports:read")
    student = _student(db, student_user_id, current_user)
    generated = db.query(models.GeneratedDocument).filter(
        models.GeneratedDocument.student_id == student.student_profile.id,
        models.GeneratedDocument.document_type == models.GeneratedDocumentType.REPORT_CARD,
    ).order_by(models.GeneratedDocument.generated_at.desc()).first()
    if generated:
        generated.downloaded_at = __import__("datetime").datetime.utcnow()
        audit.record_audit(db, action="automation.document.downloaded", current_user=current_user, entity_type="generated_document", entity_id=generated.id, details={"type": "report_card"})
        db.commit()
    grades = db.query(models.Grade).filter(models.Grade.student_id == student.student_profile.id).all()
    lines = [
        f"Student: {student.full_name}",
        f"Matricule: {student.student_profile.registration_number}",
        f"Class: {student.student_profile.current_class.name if student.student_profile.current_class else '-'}",
        f"Locale: {student.school.primary_language if student.school else 'fr'}",
        "",
    ]
    if grades:
        for grade in grades:
            assessment = grade.assessment
            lines.append(f"{assessment.subject.name if assessment and assessment.subject else '-'} / {assessment.title if assessment else '-'}: {grade.score}")
    else:
        lines.append("No grades recorded.")
    return Response(pdf.professional_pdf("Bulletin scolaire", lines, f"VERIFY:report-card:{student.student_profile.id}:{student.student_profile.registration_number}"), media_type="application/pdf")


@router.get("/portal")
def portal_documents(
    student_id: int | None = None,
    document_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    allowed_student_ids: list[int] = []
    if current_user.role in [models.UserRole.STUDENT, models.UserRole.PUPIL] and current_user.student_profile:
        allowed_student_ids = [current_user.student_profile.id]
    elif current_user.role == models.UserRole.PARENT:
        allowed_student_ids = [
            row.student_id for row in db.query(models.ParentStudentLink).filter(
                models.ParentStudentLink.parent_user_id == current_user.id,
                models.ParentStudentLink.is_active == True,
            ).all()
        ]
    else:
        rbac.require_permission(current_user, "files:read", db)
        if current_user.school_id:
            allowed_student_ids = [
                row.id for row in db.query(models.StudentProfile).join(models.User).filter(models.User.school_id == current_user.school_id).all()
            ]
    if student_id:
        if allowed_student_ids and student_id not in allowed_student_ids:
            raise HTTPException(status_code=403, detail="Not authorized for this student")
        allowed_student_ids = [student_id]
    doc_query = db.query(models.GeneratedDocument).filter(models.GeneratedDocument.school_id == current_user.school_id)
    notif_query = db.query(models.NotificationHistory).filter(models.NotificationHistory.school_id == current_user.school_id)
    if allowed_student_ids:
        doc_query = doc_query.filter(models.GeneratedDocument.student_id.in_(allowed_student_ids))
        notif_query = notif_query.filter(models.NotificationHistory.student_id.in_(allowed_student_ids))
    if document_type:
        doc_query = doc_query.filter(models.GeneratedDocument.document_type == document_type)
    if start_date:
        doc_query = doc_query.filter(models.GeneratedDocument.generated_at >= start_date)
        notif_query = notif_query.filter(models.NotificationHistory.created_at >= start_date)
    if end_date:
        doc_query = doc_query.filter(models.GeneratedDocument.generated_at <= end_date)
        notif_query = notif_query.filter(models.NotificationHistory.created_at <= end_date)
    documents = doc_query.order_by(models.GeneratedDocument.generated_at.desc()).limit(500).all()
    notifications = notif_query.order_by(models.NotificationHistory.created_at.desc()).limit(500).all()
    invoices = db.query(models.StudentInvoice).filter(models.StudentInvoice.school_id == current_user.school_id)
    balances = db.query(models.OutstandingBalance).filter(models.OutstandingBalance.school_id == current_user.school_id)
    if allowed_student_ids:
        invoices = invoices.filter(models.StudentInvoice.student_id.in_(allowed_student_ids))
        balances = balances.filter(models.OutstandingBalance.student_id.in_(allowed_student_ids))
    return {
        "documents": [
            {
                "id": doc.id,
                "document_type": doc.document_type.value,
                "title": doc.title,
                "reference": doc.reference,
                "student_id": doc.student_id,
                "generated_at": doc.generated_at,
                "download_url": doc.download_url,
            }
            for doc in documents
        ],
        "notifications": [
            {
                "id": row.id,
                "event_type": row.event_type,
                "subject": row.subject,
                "message": row.message,
                "channel": row.channel,
                "student_id": row.student_id,
                "created_at": row.created_at,
            }
            for row in notifications
        ],
        "invoices": [
            {
                "id": row.id,
                "invoice_number": row.invoice_number,
                "title": row.title,
                "amount_due": row.amount_due,
                "amount_paid": row.amount_paid,
                "remaining_balance": row.remaining_balance,
                "status": row.status.value,
                "student_id": row.student_id,
            }
            for row in invoices.order_by(models.StudentInvoice.created_at.desc()).limit(500).all()
        ],
        "balances": [
            {
                "id": row.id,
                "amount_due": row.amount_due,
                "amount_paid": row.amount_paid,
                "remaining_balance": row.remaining_balance,
                "status": row.status.value,
                "student_id": row.student_id,
            }
            for row in balances.order_by(models.OutstandingBalance.updated_at.desc()).limit(500).all()
        ],
    }


@router.get("/diplomas/{diploma_id}.pdf")
def diploma_pdf(diploma_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    rbac.require_permission(current_user, "documents:issue")
    query = db.query(models.DiplomaRecord).filter(models.DiplomaRecord.id == diploma_id)
    if current_user.school_id:
        query = query.filter(models.DiplomaRecord.school_id == current_user.school_id)
    diploma = query.first()
    if not diploma:
        raise HTTPException(status_code=404, detail="Diploma not found")
    student = diploma.student.user if diploma.student and diploma.student.user else None
    lines = [
        f"Student: {student.full_name if student else '-'}",
        f"Diploma: {diploma.diploma_name}",
        f"Mention: {diploma.mention or '-'}",
        f"Certificate number: {diploma.certificate_number}",
        f"Credits: {diploma.total_credits}",
        f"Issued date: {diploma.issued_date}",
        f"Certified: {'yes' if diploma.is_certified else 'no'}",
        f"Verification: /documents/verify/diploma/{diploma.id}?code={diploma.certificate_number}",
        f"QR payload: VERIFY:diploma:{diploma.id}:{diploma.certificate_number}",
    ]
    return Response(pdf.professional_pdf("Diplome certifie", lines, f"/documents/verify/diploma/{diploma.id}?code={diploma.certificate_number}"), media_type="application/pdf")
