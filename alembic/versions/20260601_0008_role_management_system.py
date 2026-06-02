"""role management system

Revision ID: 20260601_0008
Revises: 20260601_0007
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0008"
down_revision = "20260601_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for value in [
            "admin",
            "accountant",
            "receptionist",
            "secretary",
            "director",
            "principal",
            "department_head",
            "pedagogy_coordinator",
            "educator",
            "trainer",
            "instructor",
            "pupil",
        ]:
            op.execute(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{value}'")
    op.create_table(
        "role_definitions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("key", sa.String(), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(), nullable=False, server_default="#0F766E"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("parent_role_key", sa.String(), nullable=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True, index=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("key", "school_id", name="_role_definition_scope_uc"),
    )
    op.create_table(
        "role_permission_matrix",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("role_key", sa.String(), nullable=False, index=True),
        sa.Column("module", sa.String(), nullable=False, index=True),
        sa.Column("action", sa.String(), nullable=False, index=True),
        sa.Column("permission", sa.String(), nullable=False, index=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True, index=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("role_key", "permission", "school_id", name="_role_permission_matrix_scope_uc"),
    )
    op.create_table(
        "user_role_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("role_key", sa.String(), nullable=False, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True, index=True),
        sa.Column("assigned_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "role_key", "school_id", name="_user_role_assignment_uc"),
    )


def downgrade() -> None:
    op.drop_table("user_role_assignments")
    op.drop_table("role_permission_matrix")
    op.drop_table("role_definitions")
