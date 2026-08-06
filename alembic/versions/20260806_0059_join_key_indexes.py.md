# 20260806_0059_join_key_indexes.py
## Source File
- `alembic/versions/20260806_0059_join_key_indexes.py`
## Purpose
- Second-pass audit (PERF-06): migration 0058 indexed the SCOPE keys
  (school_id, student_id, class_id...) but missed the JOIN keys on the tables
  that grow every day. Adds 13 indexes: attendance.timetable_id/recorded_by_id,
  grades.assessment_id, assignment_submissions.assignment_id/graded_by_id,
  payments.fee_id/recorded_by_id, student_invoices.created_by_id,
  audit_logs.actor_id, security_events.actor_id,
  notification_history.created_by_id, ai_usage_logs.provider_id,
  student_cv_access_logs.recruiter_id. Index-only, additive, idempotent.
## Verification
- `python -m alembic upgrade head` (applied; attendance.timetable_id,
  grades.assessment_id and payments.fee_id verified present).
