# employment.py

## Source File

- `backend/routers/employment.py`

## Purpose

- Exposes TeducAI Emploi APIs for public CV sharecode lookup, sector search, external student registration, recruiter registration, student CV management, work history, recommendations, AI agents, recruiter subscriptions, AI credits, advanced job offers, matching, notifications, applications, interviews, and Super Admin employment oversight.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Public sharecode lookup must not reveal private school, finance, payment, AI credit, family, or internal disciplinary data.
- Public profile/search endpoints must honor an authenticated pending recruiter's payment restriction when a bearer token is present.
- Authenticated student endpoints may create or update only the connected user's CV.
- Student CV photos and recruiter logos are uploaded as JPG, PNG, or WebP files through SecureFile-backed endpoints, then exposed through public read routes only for share-enabled CVs or active recruiters.
- Recruiter endpoints must stay limited to the connected recruiter's profile, offers, applications, and interviews.
- Recruiter registration logs sanitized payloads, validation milestones, database row creation, side-effect failures, and stack traces on failure; passwords must never be logged.
- The `/agent` endpoint consumes AI credits like the dashboard chat: it checks the caller's balance before generation (no charge if insufficient) and records usage (`module_name="employment_agent"`) against the caller's wallet afterwards.
- Recruiter registration must return JSON `HTTPException` details for validation, integrity, and server failures instead of plain-text Uvicorn 500 responses.
- New recruiter users use `UserRole.RECRUITER` only when the PostgreSQL enum contains the SQLAlchemy-stored `RECRUITER` label; `RecruiterProfile` remains authoritative and keeps older/fallback `staff` rows routable as recruiters.
- Core recruiter account/profile creation must not fail solely because payment or audit side-effect rows fail; those failures are logged after the core account is committed.
- Recruiters with `payment_status != confirmed` may read their dashboard profile and own offer list, but premium actions such as creating/updating/deleting offers, viewing CV/profile search results, viewing applications, or creating interviews must return a clean 402 payment-required message.
- Super Admin employment endpoints must require `UserRole.SUPER_ADMIN` and expose operational summaries without bypassing recruiter/student ownership rules on mutating endpoints.
- Super Admin employment overview stats expose frontend-consumed keys (`students`, `recruiters`, `active_jobs`, `pending_recruiters`, `applications`) and legacy aliases where useful; counts must come from live database queries.
- Job publication computes deterministic candidate match scores, stores an offer summary, and creates employment notifications for the recruiter and top matching students.
- Job offer API responses include recruiter/company logo URLs so public listings, recommendations, and recruiter-owned offer lists can render the company brand consistently.
- Keep audit events for CV creation/update, sharecode regeneration, job offer changes, applications, and interview invitations.

## Verification

- `python -m py_compile backend\routers\employment.py`
- `python -m pytest backend/test_employment_recruiter_registration.py`
- Run backend tests for employment flows when available.
- Automation D (recruiters): saved-search agents (`GET/POST/DELETE /recruiter/saved-searches`, `POST .../{id}/run`, `POST .../run-all` cron-friendly — watermark-idempotent, notifies only NEW matching CVs), `POST /recruiter/jobs/{id}/screening-questions` (AI questionnaire stored on the offer) and `POST /recruiter/jobs/{id}/matches/{cv_id}/explain` (AI match reasons grounded in match_score details). All recruiter-scoped + payment-gated; AI calls credit-gated in services/recruiter_agents.py.
- Automation D (job-seekers): `POST /me/cv/refresh` (real academic record into the CV on demand), `POST /me/jobs/{id}/gap-analysis` (deterministic missing skills/languages/experience + AI advice) and `POST /me/jobs/{id}/cover-letter` (AI draft grounded strictly in the CV) - published offers only, AI calls credit-gated in services/jobseeker_agents.py.
