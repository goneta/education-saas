# 20260627_0031_timetable_constraint_rules.py

## Purpose

- Creates the `timetable_constraint_rules` table backing the configurable timetable constraint engine, so scheduling rules are stored in the database and administered through the UI rather than hard-coded.

## Local Contracts

- Rules are scoped by `school_id` (and optionally `school_model_assignment_id`); `rule_type` + JSON `parameters` are interpreted by `services/timetable_constraints.py`, with a `severity` (blocking/warning) and `is_active` flag. Additive table, no backfill.

## Verification

- `python -m alembic heads`
- `python -m py_compile backend\models.py`
