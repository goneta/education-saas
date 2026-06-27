"""Teacher absences + timetable delivery mode (hybrid).

Revision ID: 20260628_0034
Revises: 20260628_0033
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0034"
down_revision = "20260628_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teacher_absences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teacher_absences_school_id"), "teacher_absences", ["school_id"], unique=False)
    op.create_index(op.f("ix_teacher_absences_teacher_id"), "teacher_absences", ["teacher_id"], unique=False)
    op.create_index(op.f("ix_teacher_absences_start_date"), "teacher_absences", ["start_date"], unique=False)

    op.add_column("timetables", sa.Column("delivery_mode", sa.String(), nullable=False, server_default="in_person"))


def downgrade() -> None:
    op.drop_column("timetables", "delivery_mode")
    op.drop_index(op.f("ix_teacher_absences_start_date"), table_name="teacher_absences")
    op.drop_index(op.f("ix_teacher_absences_teacher_id"), table_name="teacher_absences")
    op.drop_index(op.f("ix_teacher_absences_school_id"), table_name="teacher_absences")
    op.drop_table("teacher_absences")
