"""unique school registration number

Revision ID: 20260609_0014
Revises: 20260608_0013
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "20260609_0014"
down_revision = "20260608_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_schools_registration_number",
        "schools",
        ["registration_number"],
        unique=True,
        postgresql_where=sa.text("registration_number IS NOT NULL"),
        sqlite_where=sa.text("registration_number IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_schools_registration_number", table_name="schools")
