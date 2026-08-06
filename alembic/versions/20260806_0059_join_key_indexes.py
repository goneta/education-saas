"""Remaining join-key indexes on the fastest-growing tables (second-pass audit).

Migration 0058 covered the *scope* keys (school_id, student_id, class_id…).
This one covers the **join** keys that the first list missed on the tables whose
volume grows every single day — attendance, grades, submissions, payments,
audit and notification history:

- `attendance.timetable_id` is joined on every attendance query (including the
  newly paginated list endpoint);
- `grades.assessment_id` is read on every report card, every gradebook screen
  and by the deletion guard;
- `payments.fee_id` drives the outstanding-balance computation used across
  Finance (and the per-student loop in education.py);
- `assignment_submissions.assignment_id` is the grading roster;
- the `*_by_id` / `actor_id` columns back the audit and history screens.

Index-only, additive, idempotent.

Revision ID: 20260806_0059
Revises: 20260805_0058
Create Date: 2026-08-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260806_0059"
down_revision = "20260805_0058"
branch_labels = None
depends_on = None


JOIN_KEYS: list[tuple[str, str]] = [
    ("attendance", "timetable_id"),
    ("attendance", "recorded_by_id"),
    ("grades", "assessment_id"),
    ("assignment_submissions", "assignment_id"),
    ("assignment_submissions", "graded_by_id"),
    ("payments", "fee_id"),
    ("payments", "recorded_by_id"),
    ("student_invoices", "created_by_id"),
    ("audit_logs", "actor_id"),
    ("security_events", "actor_id"),
    ("notification_history", "created_by_id"),
    ("ai_usage_logs", "provider_id"),
    ("student_cv_access_logs", "recruiter_id"),
]


def _index_name(table: str, column: str) -> str:
    return f"ix_{table}_{column}"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    for table, column in JOIN_KEYS:
        if table not in tables:
            continue
        columns = {col["name"] for col in inspector.get_columns(table)}
        if column not in columns:
            continue
        existing = {tuple(idx.get("column_names") or []) for idx in inspector.get_indexes(table)}
        if (column,) in existing:
            continue
        op.create_index(_index_name(table, column), table, [column])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    for table, column in JOIN_KEYS:
        if table not in tables:
            continue
        names = {idx["name"] for idx in inspector.get_indexes(table)}
        name = _index_name(table, column)
        if name in names:
            op.drop_index(name, table_name=table)
