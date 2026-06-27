"""Multi-school teaching: teacher_assignments.

Revision ID: 20260627_0030
Revises: 20260627_0029
Create Date: 2026-06-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260627_0030"
down_revision = "20260627_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teacher_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("school_model_assignment_id", sa.Integer(), nullable=True),
        sa.Column("employment_type", sa.String(), nullable=False, server_default="full_time"),
        sa.Column("specialization", sa.String(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["school_model_assignment_id"], ["school_model_assignments.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "school_model_assignment_id", name="uq_teacher_assignment_user_model"),
    )
    op.create_index(op.f("ix_teacher_assignments_user_id"), "teacher_assignments", ["user_id"], unique=False)
    op.create_index(op.f("ix_teacher_assignments_school_id"), "teacher_assignments", ["school_id"], unique=False)
    op.create_index(op.f("ix_teacher_assignments_is_active"), "teacher_assignments", ["is_active"], unique=False)

    # Backfill: every existing teacher becomes their own primary assignment so
    # listing/scoping keeps working after the cutover. Bound boolean params keep
    # this dialect-safe (Postgres in prod, SQLite in tests).
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO teacher_assignments
                (user_id, school_id, school_model_assignment_id, employment_type, is_primary, is_active)
            SELECT tp.user_id, u.school_id, tp.school_model_assignment_id, 'full_time', :is_primary, :is_active
            FROM teacher_profiles tp
            JOIN users u ON u.id = tp.user_id
            WHERE u.school_id IS NOT NULL
            """
        ),
        {"is_primary": True, "is_active": True},
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_teacher_assignments_is_active"), table_name="teacher_assignments")
    op.drop_index(op.f("ix_teacher_assignments_school_id"), table_name="teacher_assignments")
    op.drop_index(op.f("ix_teacher_assignments_user_id"), table_name="teacher_assignments")
    op.drop_table("teacher_assignments")
