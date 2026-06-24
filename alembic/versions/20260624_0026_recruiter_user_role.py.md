# 20260624_0026_recruiter_user_role.py

## Purpose

- Adds the `recruiter` value to the production `userrole` enum for recruiter accounts created through TeducAI Emploi.

## Local Contracts

- Existing recruiter accounts that were previously created as `staff` remain supported through their `RecruiterProfile`.
- Downgrade intentionally leaves the PostgreSQL enum value in place because removing enum values requires rebuilding dependent columns.

## Verification

- `python -m alembic heads`
