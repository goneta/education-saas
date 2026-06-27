# grades.py

## Source File

- `backend/routers/grades.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.
- Owns assessment CRUD and bulk grade entry. Assessments are tenant-scoped through their class (`_assessment_in_school`): cross-school read/update/delete return 404, and creation rejects a class from another school (`_assert_class_in_school`).

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
# Student enrollment scope

Grade creation resolves the exact active enrollment and rejects writes to closed academic years or students outside the active context.

Assessment create/update/delete enforce academic-year editability (`_ensure_year_editable`); reads (`get_assessment`, `get_assessment_grades`) stay allowed on closed years so historical data remains consultable, while still being tenant-scoped.
