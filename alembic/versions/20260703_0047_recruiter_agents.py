"""Automation D: recruiter saved searches + per-offer screening questions.

Revision ID: 20260703_0047
Revises: 20260703_0046
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_0047"
down_revision = "20260703_0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recruiter_saved_searches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recruiter_id", sa.Integer(), sa.ForeignKey("recruiter_profiles.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_recruiter_saved_searches_recruiter_id", "recruiter_saved_searches", ["recruiter_id"])
    op.create_index("ix_recruiter_saved_searches_is_active", "recruiter_saved_searches", ["is_active"])
    op.add_column("job_offers", sa.Column("screening_questions", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_offers", "screening_questions")
    op.drop_index("ix_recruiter_saved_searches_is_active", table_name="recruiter_saved_searches")
    op.drop_index("ix_recruiter_saved_searches_recruiter_id", table_name="recruiter_saved_searches")
    op.drop_table("recruiter_saved_searches")
