# teachers.py

## Source File

- `backend/routers/teachers.py`

## Purpose

- Defines tenant-scoped teacher creation, listing, detail, update, deletion, and multi-school assignment endpoints.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Collection routes accept both `/teachers` and `/teachers/` without redirects.
- Teacher profiles are the list/detail source of truth so educator, trainer, instructor, or custom primary roles do not hide valid teacher records.
- Listing requires `teachers:view`, eagerly loads `teacher_profile`, applies tenant scope, and orders records deterministically.
- Teacher creation, transfer, and listing use the validated active school-model assignment.
- Multi-school teaching: listing and detail/update/delete access are driven by active `TeacherAssignment` rows, so a teacher engaged at several schools appears in each school's list. `POST /teachers/{id}/assignments` attaches an existing teacher to the caller's active context additively (keeps other schools), `GET /teachers/{id}/assignments` lists their engagements, and `DELETE /teachers/assignments/{id}` ends one school's engagement. `DELETE /teachers/{id}` ends only the caller's school assignment when the teacher still teaches elsewhere, and fully deletes the profile/user only when it was their last school. `GET /teachers/lookup?email=` resolves an existing teacher by email (admin only) so they can be added to another school.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
