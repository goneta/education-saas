"""school profile settings

Revision ID: 20260606_0010
Revises: 20260602_0009
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260606_0010"
down_revision = "20260602_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("schools", sa.Column("registration_number", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("schools", "registration_number")
