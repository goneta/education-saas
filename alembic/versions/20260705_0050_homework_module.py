"""Homework/exercise module: extend assignments + assignment_submissions.

Column-only additions (no new tables, no enum-type changes) so it applies
cleanly on both SQLite (metadata-built) and PostgreSQL. Idempotent via a
per-column guard.

Revision ID: 20260705_0050
Revises: 20260704_0049
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260705_0050"
down_revision = "20260704_0049"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column in {c["name"] for c in inspector.get_columns(table)}


def _has_index(table: str, index: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index in {i["name"] for i in inspector.get_indexes(table)}


ASSIGNMENT_COLUMNS = [
    ("assignment_type", sa.Column("assignment_type", sa.String(), nullable=False, server_default="devoir")),
    ("mode", sa.Column("mode", sa.String(), nullable=False, server_default="online")),
    ("content", sa.Column("content", sa.JSON(), nullable=True)),
    ("answer_key", sa.Column("answer_key", sa.JSON(), nullable=True)),
    ("max_score", sa.Column("max_score", sa.Float(), nullable=False, server_default="20")),
    ("open_at", sa.Column("open_at", sa.DateTime(), nullable=True)),
    ("duration_minutes", sa.Column("duration_minutes", sa.Integer(), nullable=True)),
    ("max_attempts", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="1")),
    ("late_penalty", sa.Column("late_penalty", sa.Float(), nullable=False, server_default="0")),
    ("allow_groups", sa.Column("allow_groups", sa.Boolean(), nullable=False, server_default=sa.false())),
    ("target_student_ids", sa.Column("target_student_ids", sa.JSON(), nullable=True)),
    ("answer_key_release", sa.Column("answer_key_release", sa.String(), nullable=False, server_default="after_due")),
    ("ai_generated", sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default=sa.false())),
    ("updated_at", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)),
]

SUBMISSION_COLUMNS = [
    ("workflow_status", sa.Column("workflow_status", sa.String(), nullable=False, server_default="draft")),
    ("answers", sa.Column("answers", sa.JSON(), nullable=True)),
    ("attachment_urls", sa.Column("attachment_urls", sa.JSON(), nullable=True)),
    ("attempt_number", sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1")),
    ("is_late", sa.Column("is_late", sa.Boolean(), nullable=False, server_default=sa.false())),
    ("ai_graded", sa.Column("ai_graded", sa.Boolean(), nullable=False, server_default=sa.false())),
    ("ai_feedback", sa.Column("ai_feedback", sa.JSON(), nullable=True)),
    ("annotations", sa.Column("annotations", sa.JSON(), nullable=True)),
    # Column-only FK (no ALTER ADD CONSTRAINT — SQLite can't alter constraints).
    ("graded_by_id", sa.Column("graded_by_id", sa.Integer(), nullable=True)),
    ("updated_at", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)),
]


def upgrade() -> None:
    for name, column in ASSIGNMENT_COLUMNS:
        if not _has_column("assignments", name):
            op.add_column("assignments", column)
    if not _has_index("assignments", "ix_assignments_assignment_type"):
        op.create_index("ix_assignments_assignment_type", "assignments", ["assignment_type"])
    for name, column in SUBMISSION_COLUMNS:
        if not _has_column("assignment_submissions", name):
            op.add_column("assignment_submissions", column)
    if not _has_index("assignment_submissions", "ix_assignment_submissions_workflow_status"):
        op.create_index("ix_assignment_submissions_workflow_status", "assignment_submissions", ["workflow_status"])


def downgrade() -> None:
    if _has_index("assignment_submissions", "ix_assignment_submissions_workflow_status"):
        op.drop_index("ix_assignment_submissions_workflow_status", table_name="assignment_submissions")
    for name, _ in reversed(SUBMISSION_COLUMNS):
        if _has_column("assignment_submissions", name):
            op.drop_column("assignment_submissions", name)
    if _has_index("assignments", "ix_assignments_assignment_type"):
        op.drop_index("ix_assignments_assignment_type", table_name="assignments")
    for name, _ in reversed(ASSIGNMENT_COLUMNS):
        if _has_column("assignments", name):
            op.drop_column("assignments", name)
