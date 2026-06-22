"""add persistent user profile photos

Revision ID: 20260622_0021
Revises: 20260622_0020
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260622_0021"
down_revision = "20260622_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "profile_photo_url" not in columns:
        op.add_column("users", sa.Column("profile_photo_url", sa.String(), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "profile_photo_url" in columns:
        op.drop_column("users", "profile_photo_url")
