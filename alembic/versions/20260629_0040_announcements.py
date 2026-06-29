"""Communication: announcements.

Revision ID: 20260629_0040
Revises: 20260629_0039
Create Date: 2026-06-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260629_0040"
down_revision = "20260629_0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("audience", sa.String(), nullable=False, server_default="all"),
        sa.Column("class_id", sa.Integer(), nullable=True),
        sa.Column("is_emergency", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_announcements_school_id"), "announcements", ["school_id"], unique=False)
    op.create_index(op.f("ix_announcements_status"), "announcements", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_announcements_status"), table_name="announcements")
    op.drop_index(op.f("ix_announcements_school_id"), table_name="announcements")
    op.drop_table("announcements")
