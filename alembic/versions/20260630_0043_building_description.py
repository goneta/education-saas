"""Facilities: building description column.

Revision ID: 20260630_0043
Revises: 20260630_0042
Create Date: 2026-06-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0043"
down_revision = "20260630_0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("buildings", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("buildings", "description")
