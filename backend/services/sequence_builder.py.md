# sequence_builder.py — Séquence builder (automation D, teachers)

## Purpose

- `list_sequence_options(db, school_id)` — the (class, subject) pairs that
  actually have `Timetable` slots (with weekly slot count + weekly minutes,
  `duration_minutes` preferred over start/end arithmetic) and the current
  year's terms.
- `build_sequence(db, school_id, current_user, *, class_id, subject_id,
  term_id, topic="", language="fr")` — generates the whole term's lesson
  sequence in ONE AI call, calibrated on real data: sessions = weekly slots ×
  the term's weeks (default 12 when the term has no usable dates). Week-by-
  week progression with per-session title/objective/activities, periodic
  formative checks and a final summative assessment.

## Rules

- **AI credits**: `ensure_credits` before, `record_usage` after (module
  `automation_sequence`).
- **Persistence**: the sequence is recorded as a `sequence.generated`
  notification to the teacher (`source_type="timetable_sequence"`), so it
  survives the page.
- **Guards**: class must belong to the school (404); pair without timetable
  slots → 422 (the sequence must stay anchored to real hours — never invent
  a volume).

## Verification

- `python -m pytest backend/test_sequence_builder.py`
