"""Configurable timetable grid: configs, holidays, subject requirements.

Revision ID: 20260628_0033
Revises: 20260628_0032
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0033"
down_revision = "20260628_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "timetable_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("school_model_assignment_id", sa.Integer(), nullable=True),
        sa.Column("working_days", sa.JSON(), nullable=False),
        sa.Column("slots", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["school_model_assignment_id"], ["school_model_assignments.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_timetable_configs_school_id"), "timetable_configs", ["school_id"], unique=False)

    op.create_table(
        "school_holidays",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_school_holidays_school_id"), "school_holidays", ["school_id"], unique=False)
    op.create_index(op.f("ix_school_holidays_date"), "school_holidays", ["date"], unique=False)

    op.create_table(
        "subject_requirements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("school_model_assignment_id", sa.Integer(), nullable=True),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(), nullable=True),
        sa.Column("weekly_sessions", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["school_model_assignment_id"], ["school_model_assignments.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subject_requirements_school_id"), "subject_requirements", ["school_id"], unique=False)
    op.create_index(op.f("ix_subject_requirements_subject_id"), "subject_requirements", ["subject_id"], unique=False)
    op.create_index(op.f("ix_subject_requirements_class_id"), "subject_requirements", ["class_id"], unique=False)


def downgrade() -> None:
    op.drop_table("subject_requirements")
    op.drop_index(op.f("ix_school_holidays_date"), table_name="school_holidays")
    op.drop_index(op.f("ix_school_holidays_school_id"), table_name="school_holidays")
    op.drop_table("school_holidays")
    op.drop_index(op.f("ix_timetable_configs_school_id"), table_name="timetable_configs")
    op.drop_table("timetable_configs")
