# 20260629_0038_departments_feature_flags.py

## Purpose

- Creates `departments` (school/campus-scoped org units) and `feature_flags` (per-institution toggles with a NULL-school platform default; unique on key+school).

## Local Contracts

- School-scoped. Feature-flag resolution = school override then platform default. Additive.

## Verification

- `python -m alembic upgrade head`; `python -m pytest backend/test_platform.py`
