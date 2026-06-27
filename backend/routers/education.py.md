# education.py

## Source File

- `backend/routers/education.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Timetable PDF exports use the shared persisted school identity and logo header.
- Timetable conflict detection combines built-in hard conflicts (class/teacher/room double-booking, time window, duration) with the admin-configurable rules evaluated by `services/timetable_constraints.py`; both `validate` and `generate` surface configured-rule violations with explanations.
- Constraint rules are managed via `/timetables/constraint-rules` (list/create/update/delete) and `/timetables/constraint-rule-types`; all are timetable-admin gated and tenant-scoped, and creation/update reject unsupported rule types and invalid severities.
- Class, subject, and academic-year collections are filtered by the validated active school-model assignment.
- System-default class and subject names are protected and those rows cannot be deleted.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
