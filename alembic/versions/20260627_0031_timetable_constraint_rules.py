"""Configurable timetable constraint rules.

Revision ID: 20260627_0031
Revises: 20260627_0030
Create Date: 2026-06-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260627_0031"
down_revision = "20260627_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "timetable_constraint_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("school_model_assignment_id", sa.Integer(), nullable=True),
        sa.Column("rule_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False, server_default="warning"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["school_model_assignment_id"], ["school_model_assignments.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_timetable_constraint_rules_school_id"), "timetable_constraint_rules", ["school_id"], unique=False)
    op.create_index(op.f("ix_timetable_constraint_rules_rule_type"), "timetable_constraint_rules", ["rule_type"], unique=False)
    op.create_index(op.f("ix_timetable_constraint_rules_is_active"), "timetable_constraint_rules", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_timetable_constraint_rules_is_active"), table_name="timetable_constraint_rules")
    op.drop_index(op.f("ix_timetable_constraint_rules_rule_type"), table_name="timetable_constraint_rules")
    op.drop_index(op.f("ix_timetable_constraint_rules_school_id"), table_name="timetable_constraint_rules")
    op.drop_table("timetable_constraint_rules")
