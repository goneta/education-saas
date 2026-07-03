"""Automation: fee_reminders tracking table.

Revision ID: 20260703_0046
Revises: 20260630_0045
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_0046"
down_revision = "20260630_0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fee_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fee_id", sa.Integer(), sa.ForeignKey("fees.id"), nullable=False),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("outstanding_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("channels", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_fee_reminders_fee_id", "fee_reminders", ["fee_id"])
    op.create_index("ix_fee_reminders_school_id", "fee_reminders", ["school_id"])
    op.create_index("ix_fee_reminders_student_id", "fee_reminders", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_fee_reminders_student_id", table_name="fee_reminders")
    op.drop_index("ix_fee_reminders_school_id", table_name="fee_reminders")
    op.drop_index("ix_fee_reminders_fee_id", table_name="fee_reminders")
    op.drop_table("fee_reminders")
