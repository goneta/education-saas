"""Core Platform: departments + feature flags.

Revision ID: 20260629_0038
Revises: 20260628_0037
Create Date: 2026-06-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260629_0038"
down_revision = "20260628_0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("campus_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("head_user_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["campus_id"], ["campuses.id"]),
        sa.ForeignKeyConstraint(["head_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_departments_school_id"), "departments", ["school_id"], unique=False)
    op.create_index(op.f("ix_departments_campus_id"), "departments", ["campus_id"], unique=False)

    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", "school_id", name="uq_feature_flag_key_school"),
    )
    op.create_index(op.f("ix_feature_flags_key"), "feature_flags", ["key"], unique=False)
    op.create_index(op.f("ix_feature_flags_school_id"), "feature_flags", ["school_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_feature_flags_school_id"), table_name="feature_flags")
    op.drop_index(op.f("ix_feature_flags_key"), table_name="feature_flags")
    op.drop_table("feature_flags")
    op.drop_index(op.f("ix_departments_campus_id"), table_name="departments")
    op.drop_index(op.f("ix_departments_school_id"), table_name="departments")
    op.drop_table("departments")
