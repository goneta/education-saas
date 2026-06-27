# test_timetable_grid.py

## Purpose

- Verifies the configurable grid service: default grid when unconfigured, config override with break/lunch excluded from schedulable slots, weekly-sessions resolution (class > level > default), and holiday lookup.

## Verification

- `python -m pytest backend/test_timetable_grid.py`
