"""super admin bootstrap fields

Revision ID: 20260610_0017
Revises: 20260610_0016
Create Date: 2026-06-10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260610_0017"
down_revision = "20260610_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(), nullable=True))
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("is_system_account", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "is_system_account")
    op.drop_column("users", "is_verified")
    op.drop_column("users", "username")
