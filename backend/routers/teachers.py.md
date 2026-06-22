# teachers.py

## Source File

- `backend/routers/teachers.py`

## Purpose

- Defines tenant-scoped teacher creation, listing, detail, update, and deletion endpoints.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Collection routes accept both `/teachers` and `/teachers/` without redirects.
- Teacher profiles are the list/detail source of truth so educator, trainer, instructor, or custom primary roles do not hide valid teacher records.
- Listing requires `teachers:view`, eagerly loads `teacher_profile`, applies tenant scope, and orders records deterministically.
- Teacher creation, transfer, and listing use the validated active school-model assignment.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
