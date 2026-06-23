# 20260623_0024_employment_cv_jobs.py

## Source File

- `alembic/versions/20260623_0024_employment_cv_jobs.py`

## Purpose

- Adds the TeducAI Emploi schema: student CVs, CV work history, recruiter profiles, employment subscription plans, job offers, applications, interviews, and CV access logs.

## DOX Scope

- Nearest contract: `alembic/versions/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Keep downgrade order opposite the dependency order.
- Seeded subscription plans are platform defaults and should remain idempotent through migration order rather than runtime model metadata.

## Verification

- `python -m alembic heads`
- `python -m alembic upgrade head` when it is safe to mutate the active database.
