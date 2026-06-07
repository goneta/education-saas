"""advanced timetable management

Revision ID: 20260607_0011
Revises: 20260606_0010
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260607_0011"
down_revision = "20260606_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("timetables", sa.Column("duration_minutes", sa.Integer(), nullable=True))
    op.add_column("timetables", sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("timetables", sa.Column("lock_scope", sa.String(), nullable=True))
    op.add_column("timetables", sa.Column("status", sa.String(), nullable=False, server_default="draft"))
    op.add_column("timetables", sa.Column("generation_batch", sa.String(), nullable=True))
    op.add_column("timetables", sa.Column("constraints_snapshot", sa.JSON(), nullable=True))
    op.add_column("timetables", sa.Column("conflict_status", sa.String(), nullable=False, server_default="clear"))
    op.add_column("timetables", sa.Column("conflict_details", sa.JSON(), nullable=True))
    op.add_column("timetables", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("timetables", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_timetables_generation_batch", "timetables", ["generation_batch"])


def downgrade() -> None:
    op.drop_index("ix_timetables_generation_batch", table_name="timetables")
    op.drop_column("timetables", "updated_at")
    op.drop_column("timetables", "published_at")
    op.drop_column("timetables", "conflict_details")
    op.drop_column("timetables", "conflict_status")
    op.drop_column("timetables", "constraints_snapshot")
    op.drop_column("timetables", "generation_batch")
    op.drop_column("timetables", "status")
    op.drop_column("timetables", "lock_scope")
    op.drop_column("timetables", "is_locked")
    op.drop_column("timetables", "duration_minutes")
