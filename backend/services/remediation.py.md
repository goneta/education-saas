# remediation.py — Auto-remédiation after assessments (automation D, teachers)

## Purpose

- `list_assessments_with_stats(db, school_id, *, limit=30)` — recent
  assessments of the school with grade stats (count, average, struggling =
  below 50% of max) so the teacher can pick where remediation is needed.
- `run_remediation(db, assessment_id, school_id, current_user, *,
  threshold_ratio=0.5, language="fr")` — for every graded student below
  `threshold_ratio x max_score`, generates a personalized practice set (3–5
  progressive exercises with hints then answers, grounded in the score and
  the teacher's comment on the copy) via
  `ai_service.generate_response_from_config` (provider-backed or local
  fallback) and delivers it as a `remediation.assigned` notification to the
  student.

## Rules

- **AI credits**: each generation is gated by `ai_credits.ensure_credits` and
  recorded with `ai_credits.record_usage` (module `automation_remediation`) —
  per the routers/AGENTS.md metering rule.
- **Idempotent per (assessment, student)**: an existing `remediation.assigned`
  notification with `source_type="assessment"` skips the student, so re-runs
  after new grades only serve newcomers.
- **Tenant scope**: the assessment must belong to a class of the caller's
  school (404 otherwise).

## Verification

- `python -m pytest backend/test_remediation.py`
