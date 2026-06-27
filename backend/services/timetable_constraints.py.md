# timetable_constraints.py

## Source File

- `backend/services/timetable_constraints.py`

## Purpose

- Configurable timetable constraint engine: evaluates a candidate course placement against the school's active `TimetableConstraintRule` rows and returns explainable violations (each with `message`, `severity`, `rule_id`). No pedagogical rule is hard-coded.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Rules dispatch by `rule_type` via the `HANDLERS` map; `SUPPORTED_RULE_TYPES` is the authoritative list used by the API to validate rule types. Add a handler + entry to support a new rule.
- Phase 1 handlers: subject_time_window, subject_no_consecutive_days, subject_after_forbidden, teacher_available_days, subject_max_per_day, max_heavy_subjects_per_day, room_subject_restriction. Each reads only its JSON `parameters` (subject/teacher ids, days, times, coefficients) — never hard-coded values.
- The engine is additive to the built-in hard conflicts (class/teacher/room double-booking, time window) enforced in `routers/education.py`; it must remain side-effect free (pure evaluation).

## Verification

- python -m py_compile backend\services\timetable_constraints.py; python -m pytest backend/test_timetable_constraints.py
