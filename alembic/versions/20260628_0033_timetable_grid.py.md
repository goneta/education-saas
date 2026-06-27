# 20260628_0033_timetable_grid.py

## Purpose

- Creates `timetable_configs` (working days + slots), `school_holidays` (non-working days), and `subject_requirements` (weekly volume per subject/class/level) backing the configurable scheduling grid.

## Local Contracts

- All three tables are school-scoped (configs/requirements optionally model-scoped). Additive; defaults are supplied in code so generation works before any row exists.

## Verification

- `python -m alembic heads`
- `python -m py_compile backend\models.py`
