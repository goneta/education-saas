# 20260705_0050_homework_module.py

Extends `assignments` (assignment_type, mode, content, answer_key, max_score,
open_at, duration_minutes, max_attempts, late_penalty, allow_groups,
target_student_ids, answer_key_release, ai_generated, updated_at) and
`assignment_submissions` (workflow_status, answers, attachment_urls,
attempt_number, is_late, ai_graded, ai_feedback, annotations, graded_by_id,
updated_at). Column-only (no new tables, no enum-type change, column-only FK)
so it applies on SQLite + Postgres; per-column/index guards keep it idempotent
on metadata-built DBs. Verified: full chain applies in-process, zero drift.
