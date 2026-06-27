# 20260628_0034_absences_delivery_mode.py

## Purpose

- Creates `teacher_absences` (recorded absences for substitution/replanning) and adds `timetables.delivery_mode` (in_person/remote/hybrid).

## Local Contracts

- School-scoped absences. `delivery_mode` defaults to `in_person`; additive column.

## Verification

- `python -m alembic heads`
- `python -m py_compile backend\models.py`
