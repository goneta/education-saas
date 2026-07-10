# main.py

## Source File

- `backend/main.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Creates the FastAPI app, middleware stack, health/readiness/metrics endpoints, and registers all routers including bootstrap, multi-school context, student lifecycle, TeducAI Emploi, and the public Site CMS.
- A best-effort startup hook auto-registers AI providers from `.env.production` keys via `ai_provider_bootstrap`; failures never block boot.
- Registers the `/facilities` router (campuses, buildings, rooms, equipment) for the timetable engine.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
# Student lifecycle

The application registers the `/student-lifecycle` router for global student profiles, enrollments, transfers, academic locks, historical edit grants, and import/export.

# TeducAI Emploi

The application registers the `/employment` router for public sharecode/CV discovery and authenticated student/recruiter employment workflows.

# Site CMS

The application registers the `/site` router for the public marketing-site content (public read, Super Admin write).
- Registers the `/transport` (Smart Transport) router.
- Registers the `/payments` centralized Payment Service router (Slice 0).
- Registers the `/platform` Core Platform router (departments, feature flags, global search).
- Registers the `/sis` Student Information System router (guardians, emergency contacts, medical records).
- Registers the `/academics` router (automatic GPA).
- Registers the `/communication` router (announcement center).
- Registers the `/hr` router (staff leave self-service + approval).
- Registers the `/analytics` router (CSV export + AI insights).
- Registers the `/extensibility` router (webhooks + API keys).
- Registers the `/ai-learning` router (lesson/quiz/exam generators).
- Global `ResponseValidationError` handler: logs the exact failing field(s)/value(s) and returns a JSON 500 instead of an opaque text/plain one — a safety net so any remaining strict response field surfaces in logs rather than silently 500-ing a list.
- Registers the `/levels` router (school-levels referential).
- Registers the `/personnel` router (#7).
- Registers the `/finance/payroll` router (#7 Payroll).
- Registers the `/api/v1` public partner API router.
- Registers the `/automations` router.
- CORS default now allows BOTH http://localhost:3000 and http://127.0.0.1:3000 (they are distinct origins). Fixes the e2e login: Playwright serves the app on 127.0.0.1:3000 and calls the backend cross-origin, so a localhost-only allow-list let the simple POST /auth/token reach the server (logged 200) but blocked the preflighted GET /auth/me, so the browser fetch threw and login never redirected off /login. Production overrides via CORS_ALLOWED_ORIGINS; wildcard guard unchanged.
- Registers the assignments router (/assignments) — homework/exercise module.
- Registers the billing router (/billing) — enterprise Billing & Subscription module (unified surface over subscriptions + AI credits + platform payments).
- Registers the public verify router (/verify/{uuid}) — universal document authentication.
