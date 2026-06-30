"""Personnel scolaire: staff_profiles table.

Revision ID: 20260630_0044
Revises: 20260630_0043
Create Date: 2026-06-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0044"
down_revision = "20260630_0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("job_title", sa.String(), nullable=True),
        sa.Column("additional_roles", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_staff_profiles_user_id", "staff_profiles", ["user_id"], unique=True)
    op.create_index("ix_staff_profiles_school_id", "staff_profiles", ["school_id"])
    op.create_index("ix_staff_profiles_department_id", "staff_profiles", ["department_id"])
    op.create_index("ix_staff_profiles_status", "staff_profiles", ["status"])


def downgrade() -> None:
    op.drop_index("ix_staff_profiles_status", table_name="staff_profiles")
    op.drop_index("ix_staff_profiles_department_id", table_name="staff_profiles")
    op.drop_index("ix_staff_profiles_school_id", table_name="staff_profiles")
    op.drop_index("ix_staff_profiles_user_id", table_name="staff_profiles")
    op.drop_table("staff_profiles")
