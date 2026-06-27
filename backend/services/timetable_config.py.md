# timetable_config.py

## Source File

- `backend/services/timetable_config.py`

## Purpose

- Provides the configurable scheduling grid: working days + course/break/lunch slots (`effective_grid`), weekly subject volume (`weekly_sessions_for`), and holiday lookup (`is_holiday`). Generation reads these instead of hard-coded days/slots, with sensible defaults when nothing is configured.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- `effective_grid` returns only `course` slots as schedulable (break/lunch excluded) and falls back to `DEFAULT_WORKING_DAYS`/`DEFAULT_SLOTS`.
- `weekly_sessions_for` resolves a subject's weekly sessions preferring a class-specific `SubjectRequirement`, then a level rule, then the default.
- Holidays are date-based (for attendance/events); the weekly recurring timetable is day-of-week based, so holidays are exposed via `is_holiday`/`holiday_dates` rather than altering the weekly grid.

## Verification

- python -m py_compile backend\services\timetable_config.py; python -m pytest backend/test_timetable_grid.py
