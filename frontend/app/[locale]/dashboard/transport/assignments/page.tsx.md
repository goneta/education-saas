# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/transport/assignments/page.tsx`

## Purpose

- Student transport assignments: list + create + delete against `/transport/assignments`, linking a `StudentProfile` (from `/students`, using `student_profile.id`) to a route. This is the Student-Information-System integration (single source of truth). Uses the shared universal `TableFilter`.

## Maintenance Notes

- The student option value must be `student.student_profile.id` (the assignment's `student_id`), not the user id. The backend rejects students from another school (404).
