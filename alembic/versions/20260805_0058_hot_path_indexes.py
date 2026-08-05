"""Hot-path indexes on tenant/scope foreign keys (audit PERF-01).

Every query in this multi-tenant platform filters by `school_id`, and most
academic queries add `student_id`, `class_id`, `academic_year_id`,
`subject_id` or `teacher_id`. 98 of those foreign-key columns had no
index, so their cost grew with the volume of the WHOLE platform instead of the
institution's — invisible in staging, painful in production.

Additive and idempotent: an index is created only when the table exists and no
index already covers that single column. Index-only migration, no data change.

Revision ID: 20260805_0058
Revises: 20260805_0057
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260805_0058"
down_revision = "20260805_0057"
branch_labels = None
depends_on = None


# (table, column) pairs computed from the models at authoring time and frozen
# here, so a later model change can never silently alter this migration.
HOT_COLUMNS: list[tuple[str, str]] = [
    ("users", "school_id"),
    ("approval_workflows", "school_id"),
    ("books", "school_id"),
    ("canteen_meal_plans", "school_id"),
    ("cash_closures", "school_id"),
    ("chart_accounts", "school_id"),
    ("expenses", "school_id"),
    ("government_exports", "school_id"),
    ("inventory_items", "school_id"),
    ("journal_entries", "school_id"),
    ("leave_requests", "school_id"),
    ("notification_providers", "school_id"),
    ("reference_data", "school_id"),
    ("security_events", "school_id"),
    ("staff_contracts", "school_id"),
    ("transport_drivers", "school_id"),
    ("transport_vehicles", "school_id"),
    ("academic_programs", "school_id"),
    ("academic_years", "school_id"),
    ("audit_logs", "school_id"),
    ("bank_transactions", "school_id"),
    ("classes", "school_id"),
    ("journal_lines", "school_id"),
    ("loans", "user_id"),
    ("notification_messages", "school_id"),
    ("subjects", "school_id"),
    ("teacher_profiles", "user_id"),
    ("transport_routes", "school_id"),
    ("vendor_invoices", "school_id"),
    ("admission_applications", "school_id"),
    ("announcements", "class_id"),
    ("assignments", "class_id"),
    ("assignments", "subject_id"),
    ("assignments", "teacher_id"),
    ("assignments", "school_id"),
    ("bank_reconciliations", "school_id"),
    ("budget_forecasts", "academic_year_id"),
    ("budget_forecasts", "class_id"),
    ("budget_forecasts", "school_id"),
    ("course_materials", "class_id"),
    ("course_materials", "subject_id"),
    ("course_materials", "teacher_id"),
    ("course_materials", "school_id"),
    ("exam_sessions", "class_id"),
    ("exam_sessions", "subject_id"),
    ("exam_sessions", "school_id"),
    ("fee_schedules", "academic_year_id"),
    ("fee_schedules", "class_id"),
    ("fee_schedules", "school_id"),
    ("payroll_records", "school_id"),
    ("payroll_records", "academic_year_id"),
    ("semesters", "academic_year_id"),
    ("semesters", "school_id"),
    ("student_profiles", "user_id"),
    ("terms", "academic_year_id"),
    ("administrative_requests", "student_id"),
    ("administrative_requests", "school_id"),
    ("assessments", "class_id"),
    ("assessments", "subject_id"),
    ("canteen_subscriptions", "student_id"),
    ("canteen_subscriptions", "school_id"),
    ("certified_transcripts", "student_id"),
    ("certified_transcripts", "school_id"),
    ("course_units", "teacher_id"),
    ("course_units", "school_id"),
    ("diploma_records", "student_id"),
    ("diploma_records", "school_id"),
    ("internships", "student_id"),
    ("internships", "school_id"),
    ("parent_student_links", "student_id"),
    ("school_exits", "student_id"),
    ("school_exits", "school_id"),
    ("sms_messages", "student_id"),
    ("sms_messages", "school_id"),
    ("student_education_history", "student_id"),
    ("student_orientations", "student_id"),
    ("student_orientations", "school_id"),
    ("timetables", "class_id"),
    ("timetables", "subject_id"),
    ("timetables", "teacher_id"),
    ("transport_assignments", "student_id"),
    ("transport_assignments", "school_id"),
    ("canteen_attendance", "school_id"),
    ("course_enrollments", "student_id"),
    ("course_enrollments", "school_id"),
    ("university_schedule_slots", "school_id"),
    ("assignment_submissions", "student_id"),
    ("attendance", "student_id"),
    ("certificate_requests", "student_id"),
    ("certificate_requests", "school_id"),
    ("fees", "academic_year_id"),
    ("fees", "class_id"),
    ("fees", "student_id"),
    ("fees", "school_id"),
    ("generated_documents", "academic_year_id"),
    ("grades", "student_id"),
    ("student_registration_documents", "student_id"),
    ("cash_journal_entries", "student_id"),
]


def _index_name(table: str, column: str) -> str:
    return f"ix_{table}_{column}"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    for table, column in HOT_COLUMNS:
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
    for table, column in HOT_COLUMNS:
        if table not in tables:
            continue
        names = {idx["name"] for idx in inspector.get_indexes(table)}
        name = _index_name(table, column)
        if name in names:
            op.drop_index(name, table_name=table)
