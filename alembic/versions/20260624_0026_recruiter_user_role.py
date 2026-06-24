"""Add recruiter user role.

Revision ID: 20260624_0026
Revises: 20260623_0025
Create Date: 2026-06-24
"""

from alembic import op


revision = "20260624_0026"
down_revision = "20260623_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'recruiter'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without rebuilding all
    # dependent columns. Keeping the value is safer than risking data loss.
    pass
