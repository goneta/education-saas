# CLAUDE.md — TeducAI working notes

AI‑first, enterprise, multi‑tenant education SaaS. **FastAPI** backend + **Next.js 16
(Turbopack)** frontend. One platform; every module shares auth, RBAC, AI services,
notifications and master data (zero data duplication).

## Conventions (read before editing)

- **DOX discipline**: every source file has a sibling `<file>.md`; each directory an
  `AGENTS.md`. Read them before editing; update the `.md` for every changed file.
- **Tenancy + RBAC**: every query is school‑scoped; writes are role‑gated.
- **Migrations**: Alembic in `alembic/versions/`; run `alembic upgrade head`. Written
  against SQLite (tests) — column‑only FKs (no `ALTER TABLE ADD CONSTRAINT`).
- **Tests**: `pytest backend`. Frontend has **no `node_modules` in the sandbox** —
  verify FE by inspection (`npm run build`/lint/Playwright can't run here).
- **Response schemas are tolerant on read** (email fields are `Optional[str]`, not
  `EmailStr`) so one bad stored value never 500s a list; input schemas stay strict. A
  global `ResponseValidationError` handler logs the exact failing field.

## Architecture map (high‑level)

- Core: `auth`, `context` (active org/school/model/year), `system`, `site` (CMS),
  `platform` (departments, feature flags, global search).
- SIS: `students`, `student_lifecycle`, `sis` (guardians, emergency contacts, medical).
- Academic: `education` (classes/subjects/timetable engine/pedagogy), `grades`,
  `attendance`, `academics` (GPA).
- AI: `chat` + `services/ai_agents.py` (41 agents, LLM router), `ai_service`,
  `ai_automation`, `ai_credits`, `ai_learning` (lesson/quiz/exam generators).
- Finance: `finance`, `services/commerce.py`, **centralized Payment Service**
  (`services/payment_service.py` + `routers/payments.py`): Stripe/CinetPay/Djamo/cash,
  idempotent confirmation, signed webhooks.
- Smart Transport: `routers/transport.py` — fleet, drivers, vehicles, routes, bus
  stops (GPS), assignments, GPS positions, boarding attendance, incidents, fuel, AI
  route optimizer, transport→Finance billing.
- Comms `communication` (announcements) · HR `hr` (leave approval) · Analytics
  `analytics` (CSV export + AI insights) · Extensibility `extensibility` (webhooks +
  API keys).

## Timetable constraint engine (latest)

- Backend: `services/timetable_constraints.py` (7 rule types), `timetable_config`,
  `timetable_optimizer` (scored candidates), `timetable_simulation`,
  `timetable_substitution`; endpoints under `/education/timetables/*`
  (constraint‑rules, config, holidays, subject‑requirements, optimize, explain,
  simulate, absences, substitutions).
- Frontend: `components/education/timetable-constraints-panel.tsx` renders the full
  constraint UI on the Emploi du temps page (AI optimized generation, grid config,
  weekly hours, holidays, the 7 pedagogical rule types with a dynamic param form,
  always‑enforced structural constraints). Rule types/params MUST mirror the engine.

## Recent change log (most recent first)

- **Functional improvements (in progress, increment by increment)**: #3 School
  Levels referential — global, Super-Admin-managed `SchoolLevel` (`/levels` CRUD,
  delete-if-unused) consumed by class creation + the student form. Next: buildings/
  rooms UI, smart class/room rules, class details, student level→class cascade,
  personnel module, role-based dashboards, full i18n sweep.

- **Timetable constraints UI**: surfaced the constraint engine on the timetable page
  (panel above; no backend change). Now also surfaces explainable-AI (/explain), scenario
  simulation (teacher-absent / extra-working-day), energy/travel metrics (derived),
  equipment & rooms, hybrid delivery-mode distribution, and multi-campus panels.
- **Production 500 fixes**: relaxed `UserResponse.email` and `SchoolResponse.email`
  (nested in user/teacher/student lists) to tolerant `Optional[str]`; cart
  `metadata_json` non‑dict normalized; global `ResponseValidationError` handler;
  `Élèves` label; student‑table self‑healing in `DashboardUxEnhancer`; robust e2e
  login locator (ids, not translated text).
- **Goal Forge slices 0–8**: Payment Service hardening; Core Platform (departments,
  feature flags, global search); SIS gaps; GPA; Communication; HR leave; Analytics;
  Extensibility; AI Learning generators. `SPEC.md`/`GOAL.md` hold scope + NOT‑READY
  items (live payments, infra/K8s, native mobile, real‑time GPS, GraphQL/marketplace).
- **Smart Transport** module (promoted out of Operations) + universal `TableFilter`
  rollout + Global Institution Context selector + 41 AI agents.

## NOT READY (need decisions/credentials/infra — never faked)

Live payment operability (real keys/webhook secrets), WhatsApp/voice/video providers,
real‑time GPS push (MQTT/WebSocket) + facial recognition + native mobile apps,
async webhook sender/GraphQL/marketplace/SDK, PDF/Excel export, Docker/K8s/HA/tracing
and the 100k‑users/300ms load targets. See `SPEC.md` §5.
