from datetime import datetime, time
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import audit, models


def _now() -> datetime:
    return datetime.utcnow()


def _invoice_status(amount_due: float, amount_paid: float, due_date: datetime | None) -> models.StudentInvoiceStatus:
    remaining = max((amount_due or 0) - (amount_paid or 0), 0)
    if remaining <= 0:
        return models.StudentInvoiceStatus.PAID
    if amount_paid and amount_paid > 0:
        return models.StudentInvoiceStatus.PARTIAL
    if due_date and due_date < _now():
        return models.StudentInvoiceStatus.OVERDUE
    return models.StudentInvoiceStatus.UNPAID


def _parent_link(db: Session, student_id: int | None) -> models.User | None:
    if not student_id:
        return None
    link = db.query(models.ParentStudentLink).filter(
        models.ParentStudentLink.student_id == student_id,
        models.ParentStudentLink.is_active == True,
    ).first()
    return link.parent if link else None


def _document_exists(db: Session, source_type: str, source_id: int, document_type: models.GeneratedDocumentType) -> bool:
    return db.query(models.GeneratedDocument).filter(
        models.GeneratedDocument.source_type == source_type,
        models.GeneratedDocument.source_id == source_id,
        models.GeneratedDocument.document_type == document_type,
    ).first() is not None


def ensure_invoice_for_fee(db: Session, fee: models.Fee, current_user: models.User | None = None) -> models.StudentInvoice:
    total_paid = sum(payment.amount for payment in fee.payments)
    remaining = max(fee.amount - total_paid, 0)
    status = _invoice_status(fee.amount, total_paid, fee.due_date)
    invoice = db.query(models.StudentInvoice).filter(
        models.StudentInvoice.fee_id == fee.id,
        models.StudentInvoice.school_id == fee.school_id,
    ).first()
    created = False
    if not invoice:
        created = True
        invoice = models.StudentInvoice(
            invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}",
            source_type="fee",
            source_id=fee.id,
            fee_id=fee.id,
            student_id=fee.student_id,
            student_enrollment_id=fee.student_enrollment_id,
            school_id=fee.school_id,
            school_model_assignment_id=fee.school_model_assignment_id,
            created_by_id=current_user.id if current_user else None,
        )
        db.add(invoice)
    invoice.title = fee.title
    invoice.amount_due = fee.amount
    invoice.amount_paid = total_paid
    invoice.remaining_balance = remaining
    invoice.due_date = fee.due_date
    invoice.status = status
    invoice.student_id = fee.student_id
    invoice.student_enrollment_id = fee.student_enrollment_id
    db.flush()
    ensure_outstanding_balance(db, invoice, fee)
    ensure_generated_document(
        db,
        document_type=models.GeneratedDocumentType.INVOICE,
        title=f"Facture - {fee.title}",
        reference=invoice.invoice_number,
        source_type="invoice",
        source_id=invoice.id,
        student_id=fee.student_id,
        school_id=fee.school_id,
        student_enrollment_id=fee.student_enrollment_id,
        current_user=current_user,
        content={"amount_due": invoice.amount_due, "amount_paid": invoice.amount_paid, "remaining_balance": invoice.remaining_balance, "status": invoice.status.value},
    )
    audit.record_audit(
        db,
        action="automation.invoice.created" if created else "automation.invoice.updated",
        current_user=current_user,
        entity_type="student_invoice",
        entity_id=invoice.id,
        details={"fee_id": fee.id, "status": invoice.status.value, "remaining_balance": remaining},
    )
    return invoice


def ensure_outstanding_balance(db: Session, invoice: models.StudentInvoice, fee: models.Fee | None = None) -> models.OutstandingBalance:
    balance = db.query(models.OutstandingBalance).filter(
        models.OutstandingBalance.invoice_id == invoice.id,
        models.OutstandingBalance.school_id == invoice.school_id,
    ).first()
    if not balance:
        balance = models.OutstandingBalance(
            invoice_id=invoice.id,
            fee_id=fee.id if fee else invoice.fee_id,
            student_id=invoice.student_id,
            student_enrollment_id=invoice.student_enrollment_id,
            school_id=invoice.school_id,
            school_model_assignment_id=invoice.school_model_assignment_id,
        )
        db.add(balance)
    balance.amount_due = invoice.amount_due
    balance.amount_paid = invoice.amount_paid
    balance.remaining_balance = invoice.remaining_balance
    balance.due_date = invoice.due_date
    balance.status = invoice.status
    if invoice.amount_paid:
        balance.last_payment_at = _now()
    return balance


def ensure_generated_document(
    db: Session,
    *,
    document_type: models.GeneratedDocumentType,
    title: str,
    reference: str | None,
    source_type: str,
    source_id: int,
    student_id: int | None,
    school_id: int,
    student_enrollment_id: int | None = None,
    current_user: models.User | None = None,
    content: dict | None = None,
    download_url: str | None = None,
) -> models.GeneratedDocument:
    document = db.query(models.GeneratedDocument).filter(
        models.GeneratedDocument.source_type == source_type,
        models.GeneratedDocument.source_id == source_id,
        models.GeneratedDocument.document_type == document_type,
        models.GeneratedDocument.school_id == school_id,
    ).first()
    created = False
    if not document:
        created = True
        document = models.GeneratedDocument(
            document_type=document_type,
            source_type=source_type,
            source_id=source_id,
            student_id=student_id,
            student_enrollment_id=student_enrollment_id,
            school_id=school_id,
            generated_by_id=current_user.id if current_user else None,
        )
        db.add(document)
    document.title = title
    document.reference = reference
    document.content = content
    document.download_url = download_url
    parent = _parent_link(db, student_id)
    document.parent_user_id = parent.id if parent else None
    db.flush()
    if created:
        audit.record_audit(db, action="automation.document.generated", current_user=current_user, entity_type="generated_document", entity_id=document.id, details={"type": document_type.value, "source": source_type, "source_id": source_id})
    return document


def record_notification(
    db: Session,
    *,
    event_type: str,
    message: str,
    school_id: int,
    student_id: int | None = None,
    recipient_user: models.User | None = None,
    recipient_contact: str | None = None,
    subject: str | None = None,
    channel: str = "system",
    source_type: str | None = None,
    source_id: int | None = None,
    current_user: models.User | None = None,
) -> models.NotificationHistory:
    row = models.NotificationHistory(
        event_type=event_type,
        recipient_user_id=recipient_user.id if recipient_user else None,
        recipient_name=recipient_user.full_name if recipient_user else None,
        recipient_contact=recipient_contact,
        channel=channel,
        subject=subject,
        message=message,
        student_id=student_id,
        source_type=source_type,
        source_id=source_id,
        school_id=school_id,
        created_by_id=current_user.id if current_user else None,
    )
    db.add(row)
    audit.record_audit(db, action="automation.notification.recorded", current_user=current_user, entity_type="notification_history", details={"event_type": event_type, "student_id": student_id, "source_type": source_type, "source_id": source_id})
    return row


def ensure_cash_journal_for_payment(db: Session, payment: models.Payment, fee: models.Fee, current_user: models.User | None = None) -> None:
    if db.query(models.CashJournalEntry).filter(models.CashJournalEntry.payment_id == payment.id).first():
        return
    db.add(models.CashJournalEntry(
        entry_date=payment.payment_date or _now(),
        entry_type="payment",
        amount=payment.amount,
        reference=payment.receipt_number,
        description=f"Encaissement {fee.title}",
        payment_id=payment.id,
        student_id=fee.student_id,
        student_enrollment_id=fee.student_enrollment_id,
        operator_id=payment.recorded_by_id,
        school_id=fee.school_id,
        school_model_assignment_id=fee.school_model_assignment_id,
    ))
    audit.record_audit(db, action="automation.cash_journal.created", current_user=current_user, entity_type="payment", entity_id=payment.id, details={"amount": payment.amount})


def ensure_expense_journal_entry(db: Session, expense: models.Expense, current_user: models.User | None = None) -> None:
    if db.query(models.JournalEntry).filter(models.JournalEntry.source_type == "expense", models.JournalEntry.source_id == expense.id, models.JournalEntry.school_id == expense.school_id).first():
        return
    cash = _account(db, expense.school_id, "571", "Caisse", "asset")
    expense_account = _account(db, expense.school_id, "628", "Charges diverses", "expense")
    entry = models.JournalEntry(
        entry_date=expense.date or _now(),
        reference=f"EXP-{expense.id}",
        description=f"Depense - {expense.title}",
        source_type="expense",
        source_id=expense.id,
        school_id=expense.school_id,
        created_by_id=current_user.id if current_user else None,
    )
    entry.lines = [
        models.JournalLine(account_id=expense_account.id, label=expense.title, debit=expense.amount, credit=0, school_id=expense.school_id),
        models.JournalLine(account_id=cash.id, label="Sortie caisse", debit=0, credit=expense.amount, school_id=expense.school_id),
    ]
    db.add(entry)
    db.add(models.CashJournalEntry(
        entry_date=expense.date or _now(),
        entry_type="expense",
        amount=-abs(expense.amount),
        reference=f"EXP-{expense.id}",
        description=expense.title,
        expense_id=expense.id,
        operator_id=current_user.id if current_user else None,
        school_id=expense.school_id,
    ))
    audit.record_audit(db, action="automation.accounting_entry.created", current_user=current_user, entity_type="expense", entity_id=expense.id, details={"amount": expense.amount})


def _account(db: Session, school_id: int, code: str, name: str, account_type: str) -> models.ChartAccount:
    account = db.query(models.ChartAccount).filter(models.ChartAccount.school_id == school_id, models.ChartAccount.code == code).first()
    if account:
        return account
    account = models.ChartAccount(code=code, name=name, account_type=account_type, school_id=school_id)
    db.add(account)
    db.flush()
    return account


def refresh_financial_snapshot(db: Session, school_id: int) -> None:
    today = datetime.utcnow().date()
    period_key = today.strftime("%Y-%m")
    snapshot = db.query(models.FinancialReportSnapshot).filter(
        models.FinancialReportSnapshot.school_id == school_id,
        models.FinancialReportSnapshot.period_key == period_key,
    ).first()
    if not snapshot:
        snapshot = models.FinancialReportSnapshot(period_key=period_key, school_id=school_id)
        db.add(snapshot)
    total_invoiced = db.query(func.coalesce(func.sum(models.StudentInvoice.amount_due), 0)).filter(models.StudentInvoice.school_id == school_id).scalar() or 0
    total_paid = db.query(func.coalesce(func.sum(models.Payment.amount), 0)).join(models.Fee).filter(models.Fee.school_id == school_id).scalar() or 0
    total_expenses = db.query(func.coalesce(func.sum(models.Expense.amount), 0)).filter(models.Expense.school_id == school_id).scalar() or 0
    total_outstanding = db.query(func.coalesce(func.sum(models.OutstandingBalance.remaining_balance), 0)).filter(models.OutstandingBalance.school_id == school_id).scalar() or 0
    cash_total = db.query(func.coalesce(func.sum(models.CashJournalEntry.amount), 0)).filter(models.CashJournalEntry.school_id == school_id).scalar() or 0
    snapshot.total_invoiced = total_invoiced
    snapshot.total_paid = total_paid
    snapshot.total_expenses = total_expenses
    snapshot.total_outstanding = total_outstanding
    snapshot.cash_total = cash_total
    snapshot.payload = {
        "period": period_key,
        "generated_at": datetime.utcnow().isoformat(),
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_expenses": total_expenses,
        "total_outstanding": total_outstanding,
        "cash_total": cash_total,
    }


def automate_fee_change(db: Session, fee: models.Fee, current_user: models.User | None = None) -> None:
    ensure_invoice_for_fee(db, fee, current_user)
    refresh_financial_snapshot(db, fee.school_id)
    if fee.remaining_balance > 0 and fee.due_date and fee.due_date < _now():
        parent = _parent_link(db, fee.student_id)
        record_notification(
            db,
            event_type="payment_overdue",
            subject="Retard de paiement",
            message=f"Le solde restant pour {fee.title} est de {fee.remaining_balance:,.0f}.",
            school_id=fee.school_id,
            student_id=fee.student_id,
            recipient_user=parent,
            recipient_contact=fee.student.parent_phone if fee.student else None,
            source_type="fee",
            source_id=fee.id,
            current_user=current_user,
        )


def automate_payment(db: Session, payment: models.Payment, fee: models.Fee, current_user: models.User | None = None) -> None:
    ensure_cash_journal_for_payment(db, payment, fee, current_user)
    invoice = ensure_invoice_for_fee(db, fee, current_user)
    ensure_generated_document(
        db,
        document_type=models.GeneratedDocumentType.RECEIPT,
        title=f"Recu - {fee.title}",
        reference=payment.receipt_number,
        source_type="payment",
        source_id=payment.id,
        student_id=fee.student_id,
        school_id=fee.school_id,
        student_enrollment_id=fee.student_enrollment_id,
        current_user=current_user,
        content={"amount": payment.amount, "receipt_number": payment.receipt_number, "invoice_number": invoice.invoice_number},
        download_url=f"/documents/students/{fee.student.user_id}/receipt/{payment.id}.pdf" if fee.student else None,
    )
    parent = _parent_link(db, fee.student_id)
    record_notification(
        db,
        event_type="payment_recorded",
        subject="Paiement enregistre",
        message=f"Paiement de {payment.amount:,.0f} enregistre pour {fee.title}. Solde restant: {invoice.remaining_balance:,.0f}.",
        school_id=fee.school_id,
        student_id=fee.student_id,
        recipient_user=parent,
        recipient_contact=fee.student.parent_phone if fee.student else None,
        source_type="payment",
        source_id=payment.id,
        current_user=current_user,
    )
    refresh_financial_snapshot(db, fee.school_id)


def automate_expense(db: Session, expense: models.Expense, current_user: models.User | None = None) -> None:
    ensure_expense_journal_entry(db, expense, current_user)
    refresh_financial_snapshot(db, expense.school_id)


def automate_certificate(db: Session, certificate: models.CertificateRequest, current_user: models.User | None = None) -> None:
    ensure_generated_document(
        db,
        document_type=models.GeneratedDocumentType.CERTIFICATE,
        title=f"Attestation - {certificate.certificate_type.value}",
        reference=f"CERT-{certificate.id}",
        source_type="certificate",
        source_id=certificate.id,
        student_id=certificate.student_id,
        school_id=certificate.school_id,
        student_enrollment_id=certificate.student_enrollment_id,
        current_user=current_user,
        content={"status": certificate.status.value, "blocked_reason": certificate.blocked_reason},
        download_url=f"/documents/students/{certificate.student.user_id}/certificate/{certificate.id}.pdf" if certificate.student and certificate.student.user_id else None,
    )


def automate_report_card(db: Session, student_id: int, term_id: int | None, school_id: int, current_user: models.User | None = None) -> None:
    if _document_exists(db, "report_card", student_id, models.GeneratedDocumentType.REPORT_CARD):
        return
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    ensure_generated_document(
        db,
        document_type=models.GeneratedDocumentType.REPORT_CARD,
        title="Bulletin scolaire",
        reference=f"REPORT-{student_id}-{term_id or 'all'}",
        source_type="report_card",
        source_id=student_id,
        student_id=student_id,
        school_id=school_id,
        current_user=current_user,
        content={"term_id": term_id},
        download_url=f"/documents/students/{student.user_id}/report-card.pdf" if student and student.user_id else None,
    )
