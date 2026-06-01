"""Add global audit log table.

Revision ID: 20260601_0002
Revises: 20260601_0001
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_0002"
down_revision = "20260601_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("action", sa.String(), nullable=False, index=True),
        sa.Column("entity_type", sa.String(), nullable=True, index=True),
        sa.Column("entity_id", sa.String(), nullable=True, index=True),
        sa.Column("method", sa.String(), nullable=True),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
