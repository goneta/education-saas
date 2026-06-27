"""Platform site content CMS.

Revision ID: 20260627_0029
Revises: 20260625_0028
Create Date: 2026-06-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260627_0029"
down_revision = "20260625_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "site_content",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_site_content_id"), "site_content", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_site_content_id"), table_name="site_content")
    op.drop_table("site_content")
