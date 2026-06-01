"""RBAC overrides, accounting ledger, and LMD course enrollments.

Revision ID: 20260601_0003
Revises: 20260601_0002
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0003"
down_revision = "20260601_0002"
branch_labels = None
depends_on = None


userrole = sa.Enum("SUPER_ADMIN", "SCHOOL_ADMIN", "CASHIER", "REGISTRAR", "DIRECTION", "TEACHER", "STUDENT", "PARENT", "STAFF", name="userrole")


def upgrade():
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role", userrole, nullable=False),
        sa.Column("permission", sa.String(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role", "permission", "school_id", name="_role_permission_scope_uc"),
    )
    op.create_index(op.f("ix_role_permissions_id"), "role_permissions", ["id"], unique=False)
    op.create_index(op.f("ix_role_permissions_permission"), "role_permissions", ["permission"], unique=False)
    op.create_index(op.f("ix_role_permissions_role"), "role_permissions", ["role"], unique=False)
    op.create_index(op.f("ix_role_permissions_school_id"), "role_permissions", ["school_id"], unique=False)

    op.create_table(
        "course_enrollments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("course_unit_id", sa.Integer(), nullable=False),
        sa.Column("semester_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="registered"),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("grade", sa.String(), nullable=True),
        sa.Column("grade_point", sa.Float(), nullable=True),
        sa.Column("credits_attempted", sa.Float(), nullable=True, server_default="0"),
        sa.Column("credits_validated", sa.Float(), nullable=True, server_default="0"),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("registered_by_id", sa.Integer(), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["course_unit_id"], ["course_units.id"]),
        sa.ForeignKeyConstraint(["registered_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["semester_id"], ["semesters.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "course_unit_id", name="_student_course_unit_uc"),
    )
    op.create_index(op.f("ix_course_enrollments_id"), "course_enrollments", ["id"], unique=False)

    op.create_table(
        "journal_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entry_date", sa.DateTime(), nullable=False),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_journal_entries_entry_date"), "journal_entries", ["entry_date"], unique=False)
    op.create_index(op.f("ix_journal_entries_id"), "journal_entries", ["id"], unique=False)
    op.create_index(op.f("ix_journal_entries_reference"), "journal_entries", ["reference"], unique=False)
    op.create_index(op.f("ix_journal_entries_source_id"), "journal_entries", ["source_id"], unique=False)
    op.create_index(op.f("ix_journal_entries_source_type"), "journal_entries", ["source_type"], unique=False)

    op.create_table(
        "journal_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("debit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("credit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["chart_accounts.id"]),
        sa.ForeignKeyConstraint(["entry_id"], ["journal_entries.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_journal_lines_id"), "journal_lines", ["id"], unique=False)

    op.create_table(
        "bank_reconciliations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_transaction_id", sa.Integer(), nullable=False),
        sa.Column("journal_entry_id", sa.Integer(), nullable=True),
        sa.Column("matched_amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="matched"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("reconciled_by_id", sa.Integer(), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["bank_transaction_id"], ["bank_transactions.id"]),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["journal_entries.id"]),
        sa.ForeignKeyConstraint(["reconciled_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bank_reconciliations_id"), "bank_reconciliations", ["id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_bank_reconciliations_id"), table_name="bank_reconciliations")
    op.drop_table("bank_reconciliations")
    op.drop_index(op.f("ix_journal_lines_id"), table_name="journal_lines")
    op.drop_table("journal_lines")
    op.drop_index(op.f("ix_journal_entries_source_type"), table_name="journal_entries")
    op.drop_index(op.f("ix_journal_entries_source_id"), table_name="journal_entries")
    op.drop_index(op.f("ix_journal_entries_reference"), table_name="journal_entries")
    op.drop_index(op.f("ix_journal_entries_id"), table_name="journal_entries")
    op.drop_index(op.f("ix_journal_entries_entry_date"), table_name="journal_entries")
    op.drop_table("journal_entries")
    op.drop_index(op.f("ix_course_enrollments_id"), table_name="course_enrollments")
    op.drop_table("course_enrollments")
    op.drop_index(op.f("ix_role_permissions_school_id"), table_name="role_permissions")
    op.drop_index(op.f("ix_role_permissions_role"), table_name="role_permissions")
    op.drop_index(op.f("ix_role_permissions_permission"), table_name="role_permissions")
    op.drop_index(op.f("ix_role_permissions_id"), table_name="role_permissions")
    op.drop_table("role_permissions")
