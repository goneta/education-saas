# test_facilities.py

## Purpose

- Verifies the room lifecycle: create campus/building/room with equipment, list by type, and equipment replacement on update.
- Verifies rooms are isolated by school (another school cannot list or delete them).
- Verifies a room referenced by a timetable entry cannot be deleted.

## Verification

- `python -m pytest backend/test_facilities.py`
