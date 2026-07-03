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

- **Production hardening pass (security audit)**: removed the baked-in default
  passwords (AdmissionEnrollmentCreate schema default + frontend pre-filled
  "SecurePass2026!" in sidebar/settings forms); enroll_admission and personnel
  now auto-generate policy-compliant credentials (returned once) and validate
  caller passwords; the fallback-SECRET_KEY refusal also fires when
  .env.production exists (not only APP_ENV=production); AI chat timeout 10s->60s.
  Verified good: argon2 + enforced password policy at all creation sites,
  token-gated bootstrap, CORS wildcard refusal, rate limiting + security headers,
  encrypted provider keys, per-file access control, env files git-ignored.
  Known residual: JWT in localStorage (app-wide), async webhook sender NOT READY.

- **Public partner API + outbound webhooks (live)**: `/api/v1` read-only REST API
  authenticated by tenant API keys (`X-API-Key`, hashed, school-scoped; minted in
  `/extensibility/api-keys`) — /me, /students, /teachers, /classes, /subjects,
  /announcements. `emit_event` is now actually wired: `announcement.published`,
  `leave.decided`, `payslip.paid` queue webhook deliveries; `GET /extensibility/
  deliveries` lists them. New System → API & Integrations page (keys, webhooks,
  deliveries + retry). Docs api-webhooks page documents it; docs language dropdown
  now switches locale; timetable-integration claim corrected (transport pickup
  recalculation = roadmap). Async HTTP delivery worker remains NOT READY.

- **TeducAI Platform Docs (public docs site)**: a Claude-Docs-style documentation
  experience at `/{locale}/docs` (linked from the marketing nav, next to Tarification).
  Sticky header with top tabs, left nav sidebar + search, center content with Copy-page,
  right scroll-spy TOC, and a floating "Ask TeducAI" button; responsive (sidebar drawer
  on mobile). Content is typed data in `lib/docs/content.ts` rendered by `components/docs/*`
  (no MDX build dependency). Feature pages for the AI Timetable Engine, Cash payments &
  AI credits and Smart Transport come from the supplied feature docx; the rest are written
  from the implemented modules.

- **Audit-driven program (ongoing, increment by increment)**: (a) **UI for UI-less
  backends (#1)** — surfaced HR **Congés** (`/hr/leave-requests`: self-service request
  + role-scoped list + admin approve/reject) and **Annonces** (`/communication/
  announcements`: create/list/publish). Still UI-less: analytics, extensibility,
  ai-learning. (b) **Establishment historisation (#3)** — students (`StudentEnrollment`)
  and teachers (`TeacherAssignment`) already historised; filled the **personnel** gap
  by reusing `SchoolMembership` (`/personnel/{id}/assignments` + `/assignments/{id}/end`).
  (c) **Help Center** — context-aware (route→`?section=`); documented levels/facilities/
  personnel/payroll/leave/announcements. (d) **i18n** — Teachers/Students/Subjects lists
  + TeacherListTable via the shared `lists` namespace; payroll/leave/announcements/
  facilities/personnel/transport namespaces. Done: Teacher/Student Add/Edit modals; Finance, Operations and Grades pages now
  localized via tx()/PRODUCT_COPY. Open: other scattered legacy pages may remain; Help content: chrome i18n + locale-aware section content (loc() resolver over {fr,en,es,sw}); the 6 new-module sections translated, ~16 legacy sections still French (graceful fallback).

- **Payroll / Paie system (Finance, #7) — backend foundation**: country-extensible
  calculation engine (`services/payroll.py`), per-employee `SalaryProfile`, and
  `/finance/payroll` router (salary-profiles CRUD, payslip generate with gross→net
  breakdown + itemised lines, approve/pay method-agnostic, self-service `/payslips/me`).
  Built on the existing `PayrollRecord`/`PayrollAdjustment` (extended, nullable) so the
  legacy `/operations` payroll keeps working. Frontend (Finance UI + employee/teacher
  self-service) follows. Part of a broader audit-driven program (UI-for-backend-features,
  Help Center, establishment historisation, list/table uniformity) shipped increment by
  increment.

- **Functional improvements batch (8 modules, shipped increment by increment)**:
  (#3) global Super-Admin `SchoolLevel` referential (`/levels`, delete-if-unused);
  (#5) Buildings & Rooms UI in Gestion (`Building.description`; building PATCH/
  DELETE; rooms with type/capacity); (#6) smart class/room rules — class>room
  capacity guard on timetable entries (409), room-in-use & class-with-students
  delete guards (409), `GET /facilities/rooms/{id}/classes` + `GET /education/
  classes/{id}/students`, Nb Classes / Nb Élèves columns + "Voir" modals; (#1)
  class read-only students modal (scrollable Nom/Âge/Sexe, row→profile); (#4)
  student form level→class cascade; (#7) Personnel scolaire module (`StaffProfile`
  + `/personnel`, auto-creates the User account, roles/department/function/status);
  (#8) role-based sidebars (Teacher/Student/Parent hide admin menus; establishment
  selector already scoped server-side); (#2) i18n — new modules fully localized
  (levels/facilities/personnel/classRoster namespaces, FR/EN/ES/SW parity).
  NOTE on (#2): a full app-wide sweep of all legacy pages remains an open effort;
  only this batch's surfaces are guaranteed hardcoded-text-free.

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
