# timetable_substitution.py

## Source File

- `backend/services/timetable_substitution.py`

## Purpose

- Proposes substitute teachers for an absent teacher's courses on a weekday: for each affected course, lists teachers who are free at that slot and allowed to teach that day. Read-only (an admin applies the choice).

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- A candidate substitute must be in the school, a teaching role, not the absent teacher, not already booked on an overlapping slot that day, and allowed by any `teacher_available_days` rule.
- Applying a substitution (router `/timetables/substitutions/apply`) re-checks the slot is free before reassigning the course's teacher.

## Verification

- python -m py_compile backend\services\timetable_substitution.py; python -m pytest backend/test_timetable_substitution.py
