# test_employment_recruiter_registration.py

## Purpose

- Verifies recruiter registration creates the user, recruiter profile, platform payment, and a login session that routes to the recruiter dashboard.

## Local Contracts

- Valid recruiter registration payloads must not return HTTP 500.
- `/auth/me` must classify registered recruiters as `account_type = recruiter`.

## Verification

- `python -m pytest backend/test_employment_recruiter_registration.py`
