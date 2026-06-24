# 20260624_0027_uppercase_recruiter_user_role.py

## Purpose

- Adds the `RECRUITER` PostgreSQL enum label used by SQLAlchemy when persisting `UserRole.RECRUITER`.
- Backfills active recruiter-profile users to the uppercase enum label.

## Local Contracts

- SQLAlchemy `Enum(UserRole)` stores enum member names such as `RECRUITER`, not the lowercase Python enum value.
- The previous lowercase `recruiter` label may exist in production, but recruiter inserts require `RECRUITER`.
- Downgrade intentionally leaves the PostgreSQL enum value in place because removing enum values requires rebuilding dependent columns.

## Verification

- `python -m alembic heads`
