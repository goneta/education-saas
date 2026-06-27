# facilities.py

## Source File

- `backend/routers/facilities.py`

## Purpose

- CRUD for schedulable resources: campuses, buildings, rooms and room equipment. Feeds the timetable engine (room types/capacity/equipment) and multi-campus scheduling.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- All endpoints are tenant-scoped (`resolve_school_id_for_create`) and gated to facilities admins; cross-school access returns 404.
- Buildings validate their campus belongs to the school; rooms validate their building; room equipment is replaced wholesale on update.
- A room that is referenced by a timetable entry cannot be deleted (reassign first).

## Verification

- python -m py_compile backend\routers\facilities.py; python -c "import backend.main as m; print(m.app.title)"
- python -m pytest backend/test_facilities.py
