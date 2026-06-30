"""Referential: global school levels (Super-Admin managed).

Revision ID: 20260630_0042
Revises: 20260629_0041
Create Date: 2026-06-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0042"
down_revision = "20260629_0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "school_levels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_school_level_code"),
    )
    op.create_index(op.f("ix_school_levels_code"), "school_levels", ["code"], unique=False)
    op.create_index(op.f("ix_school_levels_sort_order"), "school_levels", ["sort_order"], unique=False)
    op.create_index(op.f("ix_school_levels_is_active"), "school_levels", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_school_levels_is_active"), table_name="school_levels")
    op.drop_index(op.f("ix_school_levels_sort_order"), table_name="school_levels")
    op.drop_index(op.f("ix_school_levels_code"), table_name="school_levels")
    op.drop_table("school_levels")
