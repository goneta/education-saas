"""Add SQLAlchemy enum label for recruiter role.

Revision ID: 20260624_0027
Revises: 20260624_0026
Create Date: 2026-06-24
"""

from alembic import op


revision = "20260624_0027"
down_revision = "20260624_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'RECRUITER'")
        op.execute(
            "UPDATE users SET role = 'RECRUITER' "
            "WHERE id IN (SELECT user_id FROM recruiter_profiles WHERE is_active = true)"
        )


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without rebuilding all
    # dependent columns. Keeping the value is safer than risking data loss.
    pass
