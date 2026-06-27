# operations.py

## Source File

- `backend/routers/operations.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.
- Owns programs, admissions/enrollment, student import, exams, inventory, payroll, transport and canteen. Every list/create/update is scoped by `_school_id`; by-id updates filter `id AND school_id` (cross-school → 404); `create_payroll` validates the staff user is in-school.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Admission enrollment assigns the student, generated fee schedules, and fees to the active school-model context.
- Admission enrollment and student import create a `StudentGlobalProfile` + `StudentEnrollment` via `student_lifecycle.ensure_current_enrollment` (using `_active_context_with_year`), so those students appear in the standard `/students` roster, which only lists students that have an enrollment.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
