# students.py

## Source File

- `backend/routers/students.py`

## Purpose

- Defines tenant-scoped student creation, listing, detail, update, deletion, history, document, and certificate endpoints.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Collection routes accept both `/students` and `/students/` without redirects.
- Student profiles are the list/detail source of truth so pupil or custom primary roles do not hide valid student records.
- Listing requires `students:view`, eagerly loads `student_profile`, applies tenant scope, and orders records deterministically.
- Deletion is logical: the user is deactivated and hidden from active list/detail APIs while dependent academic and financial history is preserved.
- Student creation, transfer, and listing use the validated active school-model assignment.
- Student creation also ensures a TeducAI Emploi CV/sharecode exists for the global student profile.
- Student detail masks unauthorized cross-tenant access as `404 Student not found` so other schools cannot infer private student existence.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
# Global lifecycle integration

Student registration creates or reuses a global profile and a context-bound enrollment. Student lists are derived from active enrollments rather than the user's legacy primary school, so transferred and concurrently enrolled students appear only in the correct active school/model/year context. Updates honor academic-year locks.
