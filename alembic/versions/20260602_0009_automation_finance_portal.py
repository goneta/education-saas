"""automation finance portal

Revision ID: 20260602_0009
Revises: 20260601_0008
Create Date: 2026-06-02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260602_0009"
down_revision = "20260601_0008"
branch_labels = None
depends_on = None


invoice_status = sa.Enum("UNPAID", "PARTIAL", "PAID", "OVERDUE", name="studentinvoicestatus")
document_type = sa.Enum("RECEIPT", "CERTIFICATE", "REPORT_CARD", "INVOICE", "TRANSCRIPT", "DIPLOMA", "OTHER", name="generateddocumenttype")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        invoice_status.create(bind, checkfirst=True)
        document_type.create(bind, checkfirst=True)

    op.create_table(
        "student_invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_number", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("amount_due", sa.Float(), nullable=False),
        sa.Column("amount_paid", sa.Float(), nullable=False, server_default="0"),
        sa.Column("remaining_balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("status", invoice_status, nullable=False, server_default="UNPAID"),
        sa.Column("source_type", sa.String(), nullable=False, server_default="fee", index=True),
        sa.Column("source_id", sa.Integer(), nullable=True, index=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True, index=True),
        sa.Column("fee_id", sa.Integer(), sa.ForeignKey("fees.id"), nullable=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False, index=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "outstanding_balances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True, index=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("student_invoices.id"), nullable=True, index=True),
        sa.Column("fee_id", sa.Integer(), sa.ForeignKey("fees.id"), nullable=True, index=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("amount_due", sa.Float(), nullable=False),
        sa.Column("amount_paid", sa.Float(), nullable=False, server_default="0"),
        sa.Column("remaining_balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", invoice_status, nullable=False, server_default="UNPAID"),
        sa.Column("last_payment_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False, index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "cash_journal_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entry_date", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column("entry_type", sa.String(), nullable=False, index=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("reference", sa.String(), nullable=True, index=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id"), nullable=True),
        sa.Column("expense_id", sa.Integer(), sa.ForeignKey("expenses.id"), nullable=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "generated_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_type", document_type, nullable=False, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("reference", sa.String(), nullable=True, index=True),
        sa.Column("source_type", sa.String(), nullable=True, index=True),
        sa.Column("source_id", sa.Integer(), nullable=True, index=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True, index=True),
        sa.Column("parent_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False, index=True),
        sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_years.id"), nullable=True),
        sa.Column("content", sa.JSON(), nullable=True),
        sa.Column("download_url", sa.String(), nullable=True),
        sa.Column("generated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "notification_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(), nullable=False, index=True),
        sa.Column("recipient_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("recipient_name", sa.String(), nullable=True),
        sa.Column("recipient_contact", sa.String(), nullable=True),
        sa.Column("channel", sa.String(), nullable=False, server_default="system"),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="recorded"),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True, index=True),
        sa.Column("source_type", sa.String(), nullable=True, index=True),
        sa.Column("source_id", sa.Integer(), nullable=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False, index=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "financial_report_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("period_key", sa.String(), nullable=False, index=True),
        sa.Column("total_invoiced", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_paid", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_expenses", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_outstanding", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cash_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False, index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("financial_report_snapshots")
    op.drop_table("notification_history")
    op.drop_table("generated_documents")
    op.drop_table("cash_journal_entries")
    op.drop_table("outstanding_balances")
    op.drop_table("student_invoices")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        document_type.drop(bind, checkfirst=True)
        invoice_status.drop(bind, checkfirst=True)
