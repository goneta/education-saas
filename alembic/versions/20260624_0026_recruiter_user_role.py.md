# 20260624_0026_recruiter_user_role.py

## Purpose

- Adds the `recruiter` value to the production `userrole` enum for recruiter accounts created through TeducAI Emploi.
- Backfills active users with recruiter profiles to the `recruiter` role after the PostgreSQL enum value is committed.
- Superseded for SQLAlchemy inserts by `20260624_0027`, which adds the uppercase `RECRUITER` enum label.

## Local Contracts

- Existing recruiter accounts that were previously created as `staff` remain supported through their `RecruiterProfile`.
- The migration uses an Alembic autocommit block before updating rows because PostgreSQL enum values cannot be safely used inside the same transaction that creates them.
- Downgrade intentionally leaves the PostgreSQL enum value in place because removing enum values requires rebuilding dependent columns.

## Verification

- `python -m alembic heads`
