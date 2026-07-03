# grade_explainer.py — Explain-my-grade (automation D, students)

## Purpose

- `list_grades_with_context(db, profile, *, limit=20)` — the student's recent
  grades with class stats (average, best, class size) and the teacher's
  comment, newest assessment first.
- `explain_grade(db, grade_id, profile, current_user, *, language="fr")` —
  on-demand AI walk-through of ONE of the student's own grades: class
  positioning (average, best, rank), reading of the teacher comment, and 2–3
  concrete improvement tips, written to the student in second person, in the
  requested language. Uses `ai_service.generate_response_from_config`
  (provider-backed or local fallback).

## Rules

- **Ownership**: the grade must belong to the resolved student (404
  otherwise); the router resolves students to themselves and parents to a
  linked child (`_student_or_linked_child` in routers/automations.py).
- **AI credits**: gated by `ai_credits.ensure_credits` and metered with
  `ai_credits.record_usage` (module `automation_explain_grade`) — charged to
  the caller (student or parent).
- Pure on-demand: nothing persisted beyond audit/usage records.

## Verification

- `python -m pytest backend/test_grade_explainer.py`
