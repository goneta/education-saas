# timetable-constraints-panel.tsx

## Source File
- `frontend/components/education/timetable-constraints-panel.tsx`

## Purpose
- The timetable constraint-configuration UI rendered on the Emploi du temps page. Collapsible sections expose the whole constraint engine to schools:
  - AI optimized generation (`/education/timetables/optimize` + `/optimize/commit`): several scored candidates, apply one.
  - Grid config (`/timetables/config`): working days + slots (course/break/lunch).
  - Weekly hours per subject (`/timetables/subject-requirements`).
  - Holidays / non-working days (`/timetables/holidays`).
  - Pedagogical constraint rules (`/timetables/constraint-rules`): the 7 engine rule types (subject_time_window, subject_no_consecutive_days, subject_after_forbidden, teacher_available_days, subject_max_per_day, max_heavy_subjects_per_day, room_subject_restriction) with a dynamic per-type param form + severity (blocking/warning).
  - An informational list of always-enforced structural constraints (no teacher/class/room double-booking).

## Local Contracts
- Rule types and parameter shapes MUST stay in sync with `backend/services/timetable_constraints.py` `HANDLERS`/`SUPPORTED_RULE_TYPES`. Payloads match the `/education/timetables/*` schemas. Reads degrade gracefully (empty) when the viewer lacks timetable-admin rights (backend 403). Receives `subjects/teachers/classes` from the page (no duplicate fetch); fetches its own constraint state.

## Verification
- cmd.exe /c "cd frontend&& npx eslint components/education/timetable-constraints-panel.tsx"; npm run build
- Also exposes: **IA explicable** (`/explain`: score + breakdown + decision bullets), **simulation de scénarios** (`/simulate`: teacher_absent / extra_working_day), **optimisation énergétique & déplacements** (metrics derived client-side from the live timetable rows — rooms used, teacher room-changes), **équipements & salles** (`/facilities/rooms`), **cours hybrides** (delivery_mode distribution), **multi-campus** (`/facilities/campuses`+`/buildings`). Derived metrics are honest read-only proxies; deeper energy/travel geodata optimization stays roadmap.
