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
- Generation reads the configurable grid (working days + course slots) and per-subject weekly volume via `services/timetable_config.py` instead of hard-coded days/slots; `/timetables/config` (get/upsert), `/timetables/holidays` and `/timetables/subject-requirements` manage these (timetable-admin gated, tenant-scoped). Break/lunch slots are excluded from scheduling.
- `/timetables/optimize` returns several scored candidate timetables (via `services/timetable_optimizer.py`) without persisting; `/timetables/optimize/commit` regenerates by seed and persists the chosen candidate as a new draft batch (respecting locks). Both are timetable-admin gated and tenant-scoped.
- `/timetables/explain` returns plain-language reasons for the best candidate's score (explainable AI); `/timetables/simulate` runs what-if scenarios (`teacher_absent`, `extra_working_day`) via `services/timetable_simulation.py` and reports the impact vs baseline.
- `/timetables/absences` records teacher absences; `/timetables/substitutions` proposes available substitutes (via `services/timetable_substitution.py`) and `/timetables/substitutions/apply` reassigns a course's teacher after re-checking the slot is free. All admin-gated + tenant-scoped.
- Class, subject, and academic-year collections are filtered by the validated active school-model assignment.
- System-default class and subject names are protected and those rows cannot be deleted.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
