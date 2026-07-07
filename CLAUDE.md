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

- **Enterprise Billing & Subscription module (foundation)**: a unified
  **Finance → Billing** page (`/dashboard/finance/billing`) — a Stripe-/OpenAI-
  style dashboard that is a *surface over the EXISTING money infra*, not a new
  money system (zero duplication). Reuses `SchoolSubscription`
  (`/system/subscription/change`), `AIWallet`/`PlatformPayment`/
  `AICreditTransaction` (`/ai_billing`) and `AuditLog`. New config tables only
  (migration 0051, new tables): `BillingPreference`, `BillingTaxProfile`,
  `WalletAutoRecharge`, `BillingPromoCode`, `BillingPromoRedemption`.
  `services/billing.py` + `routers/billing.py` (`/billing`): overview
  aggregation, plan catalog (Starter/Professional/Enterprise/Custom mirroring
  `SUBSCRIPTION_PRICES`), preferences, tax identity, auto-recharge config, promo
  validate/redeem (credits-type codes top up the school wallet + write an
  AICreditTransaction), invoices & transactions **projected** from
  `PlatformPayment`, usage (via `ai_credits.usage_summary`), billing-scoped
  audit, and Super-Admin revenue (MRR/ARR/outstanding/failed/by-country).
  RBAC: manage = admin/direction/accounting; revenue + promo authoring =
  Super-Admin only; every mutation audited (`billing.*`). Frontend page has 11
  tabs (Overview, Subscription, Payment methods, Billing history, Credits,
  Usage, Transactions, Promotions, Preferences, Tax & VAT, Audit) + CSV export;
  `billing` i18n namespace (FR/EN full, es/sw fall back to EN), sidebar Finance →
  Billing, docs page (EN+FR) + help section (4-locale) + DOX + tests
  (`test_billing.py`, 10 green). **Roadmap (documented, NOT built):** invoice
  PDF/print/email, live usage charts, saved payment-method card management UI,
  AI billing assistant — underlying data already exists.

- **Homework / exercise / correction / evaluation module (foundation)**: a
  full assignments module built on the EXISTING `Assignment` /
  `AssignmentSubmission` tables (extended column-only in migration 0050;
  `workflow_status` is a plain String so no Postgres enum-type change).
  `services/assignments.py` + `routers/assignments.py` (`/assignments`):
  11 work types, manual creation AND AI generation that also produces the
  **corrigé** (answer key: expected answers, explanations, per-question
  points, rubric — split into a student-safe `content` and the `answer_key`);
  **online** (autosave, resume, lock-after-due unless late-penalty) and
  **paper** modes; targeting a class or a student subset; submissions
  (answers + attachments, attempts, late); grading manual AND by AI (AI
  scores vs the answer key and returns comment/errors/strengths/weaknesses/
  advice — always a proposal the teacher confirms/edits); answer-key release
  control (never/after_due/immediate); a gradebook bridge
  (`push-to-gradebook` creates/reuses an Assessment + upserts Grade rows);
  per-assignment stats; notifications on publish/submit/grade to students +
  linked parents. AI calls credit-gated; nothing faked. Teacher page
  `/dashboard/assignments` (create + AI-generate + grading roster with manual/
  AI grade + push-to-gradebook) and student/parent page
  `/dashboard/my-assignments` (to-do/done/graded, online submit, corrected
  copy + corrigé when released); sidebar + 4-locale i18n + help section +
  docs page (EN+FR) + tests. **Roadmap (documented, NOT built):** rich-media
  question editor, paper-scan OCR correction wired to this module (the
  grade-scan OCR engine already exists), plagiarism / AI-answer detection,
  differentiated & variant generation, voice annotations, full analytics
  dashboards.

- **Docs site full French localization**: the public docs body was English-only
  (the language dropdown only swapped the URL locale + chrome, never the content).
  Introduced a locale-aware resolver: `lib/docs/content.ts` (English) is the
  source-of-truth/fallback, `lib/docs/content.fr.ts` holds the full French
  translation of all 26 pages + groups + tab labels + chrome strings, and
  `lib/docs/registry.ts` merges per-locale over English (per-page EN fallback,
  same graceful-fallback pattern as the Help Center). All `components/docs/*`
  now resolve via `getDocPage/getDocGroups/getTabLabel/docsUi`; group `tab`
  fields stay English (identity keys). es/sw fall back to English until their
  `content.<locale>.ts` is added.

- **Automation program (Phase 2, increment by increment)**: (A) **Relances
  impayés** — idempotent runner (`services/fee_reminders.py` + `/automations/
  fee-reminders/run|history`): scans overdue fees, 3 escalation levels (N1
  gentle notif+SMS, N2 firm, N3 urgent + admin escalation), anti-spam cooldown
  + level monotonicity via `FeeReminder` rows, SMS queued to parent phone;
  System → Automatisations UI (thresholds, run-now, summary, history). Safe to
  cron. (B) **Documents libre-service** — `/self-documents` router reusing the
  EXISTING `GeneratedDocument` table (`source_type="self_service"`, no new
  table): students/parents (via `ParentStudentLink`) generate certificat de
  scolarité, attestation and payment receipts themselves; unique verifiable
  references (CERT-/ATT-/REC-…), full payload stored for identical re-display;
  "Mes documents" page (print-ready HTML render, child selector for parents)
  in Student + Parent menus. (C) **Résumé hebdo parents + alertes de seuil** —
  `services/parent_digest.py` + `/automations/parent-digest/run|history`: one
  notification per (parent, child) in the PARENT'S language (UserPreference,
  fr/en/es/sw templates) compiling window grades (avg /20), absences/lates and
  outstanding fees; threshold alerts ride along (`parent.alert.average`,
  `parent.alert.absences`); idempotent per window (NotificationHistory
  lookback). Second card on the Automations page. (D1) **Suivi des absences +
  brief anomalies** — `services/absence_followup.py` (parent message per
  unfollowed ABSENT row, parent-language notif + SMS, once per Attendance via
  NotificationHistory source tracking) and `services/anomaly_digest.py`
  (deterministic staff brief: absence spike vs previous window, unpaid ratio,
  class-size imbalance; one brief per window). Cards 3-4 on the Automations
  page + generic `/automations/notifications/history?event_type=`. (D2)
  **Assistant de rentrée** — `services/rentree.py`: preview (dry-run plan:
  promotions per SchoolLevel sort_order, leavers, fee schedules) then run
  (new current AcademicYear, promotion to the least-filled next-level class,
  leavers archived with history kept + account active, FeeSchedule cloned);
  409 duplicate-year guard; RENTREE_ROLES = admin/direction only (no
  accountant); card 5 on the Automations page. (D3) **Planning de révision +
  rappels de devoirs** — `services/student_planner.py`: on-demand study plan
  from REAL data (class assessments, unsubmitted PUBLISHED assignments, class
  timetable) with spaced revision slots (D-5/D-2/D-1, 30/45/60 min); admin
  runner `homework-reminders/run` nudges non-submitters at D-7/D-3/D-1,
  idempotent per (assignment, student, bucket) via event type
  `homework.reminder.d7|d3|d1`. Student/Parent page `/dashboard/study-plan`
  (+ sidebar entries) and card 6 on the Automations page. (D4) **Remédiation
  IA** — `services/remediation.py`: after an assessment, one personalized
  practice set per student below the threshold (3–5 progressive exercises,
  grounded in score + teacher comment) via `ai_service.
  generate_response_from_config`, AI-credit-gated (`ensure_credits`/
  `record_usage`), delivered as `remediation.assigned` notifications,
  idempotent per (assessment, student); teacher page
  `/dashboard/remediation` (assessments stats table + threshold + expandable
  results). (D5) **Explique ma note** — `services/grade_explainer.py`:
  on-demand AI walk-through of one of the student's own grades (class
  average/best/rank + teacher-comment reading + 2–3 tips, second person, in
  the caller's UI locale), AI-credit-gated on the caller; student/parent page
  `/dashboard/explain-grade`; shared `_student_or_linked_child` resolver in
  routers/automations.py now serves study-plan + explain-grade. (D6)
  **Générateur de séquence** — `services/sequence_builder.py`: a term's full
  lesson sequence in ONE AI call, calibrated on REAL data (sessions = weekly
  Timetable slots × the term's weeks; 422 when the pair has no slots),
  credit-gated, persisted as a `sequence.generated` notification; teacher
  page `/dashboard/sequence-builder` (pair/term selectors + optional topic).
  (D7) **Automations recruteur** — `services/recruiter_agents.py` on top of
  the EXISTING `employment.match_score` engine: saved-search agents (new
  `RecruiterSavedSearch` table, migration 0047; last_run_at watermark with a
  deliberate 1-second overlap because second-resolution DB timestamps vs
  microsecond bound params would skip same-second rows; one aggregate
  EmploymentNotification per run; `run-all` endpoint cron-friendly),
  AI screening questionnaires stored on `JobOffer.screening_questions`, and
  per-candidate AI match reasons grounded strictly in match_score details;
  recruiter page gains the Questions button, "Pourquoi ?" per match and the
  saved-searches panel. (D8) **Automations chercheur d'emploi** —
  `services/jobseeker_agents.py`: `POST /me/cv/refresh` (dossier académique
  réel → CV, mécanique de year-closure exposée à l'élève), gap analysis
  (diff déterministe des compétences/langues/expérience manquantes via
  match_score + conseils IA par item) and AI cover letters grounded
  STRICTLY in the CV's real data (published offers only, credit-gated);
  student emploi page gains "Actualiser mon CV" + per-offer "Analyse
  d'écart"/"Lettre IA". (D9) **Actions parent en un clic** — `POST
  /automations/absence/{id}/justify` (linked-parent-only: ABSENT/LATE →
  EXCUSED avec remarque traçable, l'enseignant enregistreur est notifié
  `absence.justified`, 409 si déjà excusée) ; la cloche de notifications du
  header propose « Justifier l'absence » sur les `absence.followup` non lues
  et « Payer maintenant » (deep-link finance) sur fee.reminder/parent.digest
  (clés app.justifyAbsence/app.payFee, 4-locale). (D10) **Saisie de notes
  par photo (OCR)** — provider decision: OpenAI + Anthropic.
  `ai_service.generate_vision_response` (multimodal via the shared
  OpenAI-SDK clients; Anthropic spec now defaults base_url to its
  OpenAI-compatible /v1, so ANTHROPIC_API_KEY alone activates chat+vision);
  NO local fallback — 503 when no vision provider is reachable, never
  faked. `services/grade_ocr.py`: transcription-only prompt (strict JSON,
  skip unreadable), deterministic roster matching (accent/word-order-
  insensitive difflib, threshold 0.55, confidence shown), NOTHING saved by
  the scan; teacher-confirmed upsert with scale/roster 422 guards;
  credit-gated with an image surcharge. Teacher page
  `/dashboard/grade-scan` (camera capture, review table, unmatched/missing
  lists). (D11) **E-signature (in-house)** — `services/esignature.py` +
  `DocumentSignature` (migration 0048): HMAC-SHA256 keyed from a
  domain-separated derivation of SECRET_KEY over
  document|reference|content-hash|signer|timestamp; SHA-256 content hash
  freezes the document at signing (later mutation ⇒ `tampered`), forged
  signature ⇒ `authentic=False`; one signature per (document, signer), 409 on
  re-sign; student or linked parent sign self-service documents
  (`POST /self-documents/{id}/sign`), signatures ride `/mine` +
  `/verify/{reference}` and print as a verified block with a XXXX-XXXX-XXXX
  code. Integrity/authenticity signature bound to the platform account — not
  an eIDAS-qualified signature. **Phase-2 fully CLOSED (19/19).** AI provider
  order: OpenAI + Anthropic primary; OpenRouter, Manus, Genspark fallback
  (Genspark/Manus serve only once an OpenAI-compatible *_BASE_URL is
  supplied).

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
