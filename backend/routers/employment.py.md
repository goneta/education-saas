# employment.py

## Source File

- `backend/routers/employment.py`

## Purpose

- Exposes TeducAI Emploi APIs for public CV sharecode lookup, sector search, external student registration, recruiter registration, student CV management, work history, job offers, applications, and interviews.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Public sharecode lookup must not reveal private school, finance, payment, AI credit, family, or internal disciplinary data.
- Public profile/search endpoints must honor an authenticated pending recruiter's payment restriction when a bearer token is present.
- Authenticated student endpoints may create or update only the connected user's CV.
- Recruiter endpoints must stay limited to the connected recruiter's profile, offers, applications, and interviews.
- Recruiter registration logs sanitized payloads, validation milestones, database row creation, side-effect failures, and stack traces on failure; passwords must never be logged.
- Recruiter registration must return JSON `HTTPException` details for validation, integrity, and server failures instead of plain-text Uvicorn 500 responses.
- New recruiter users use `UserRole.RECRUITER` only when the database enum supports it; `RecruiterProfile` remains authoritative and keeps older/fallback `staff` rows routable as recruiters.
- Core recruiter account/profile creation must not fail solely because payment or audit side-effect rows fail; those failures are logged after the core account is committed.
- Recruiters with `payment_status != confirmed` may read their dashboard profile and own offer list, but premium actions such as creating/updating/deleting offers, viewing CV/profile search results, viewing applications, or creating interviews must return a clean 402 payment-required message.
- Keep audit events for CV creation/update, sharecode regeneration, job offer changes, applications, and interview invitations.

## Verification

- `python -m py_compile backend\routers\employment.py`
- `python -m pytest backend/test_employment_recruiter_registration.py`
- Run backend tests for employment flows when available.
