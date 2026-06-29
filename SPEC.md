# TeducAI — SPEC.md (Goal Forge settled specification)

> Produced by the Goal Forge loop (`goal-forge-loop`). This is a **planning
> artifact**, not authorization. Nothing here permits touching production,
> spending money, using real payment credentials, sending live messages, or
> deploying. Items whose inputs are not supplied are marked **NOT READY** rather
> than invented.

Status date: 2026-06-29 · Source: user "TeducAI Goal Forge — Master Feature
Definition" reconciled against the current codebase.

---

## 1. Vision (verbatim intent)

AI-first, enterprise-grade, multi-tenant education SaaS spanning preschool →
university, training centres, language schools, vocational institutes and
education groups. One platform; every module shares the **same** auth,
permissions, AI services, communication, analytics and master data. **Zero data
duplication** — modules share master data via well-defined APIs/events.

## 2. Current-state map (what already exists vs. the 10 loops)

Legend: ✅ implemented · 🟡 partial · ⬜ missing. Grounded in the repo, not assumed.

| Loop | Feature area | State | Evidence in repo |
|---|---|---|---|
| **1 Core Platform** | Multi-tenancy, Org, Campus, RBAC, permissions, audit, notifications, settings, branding, i18n, dark mode, OpenAPI | 🟡 | `models.Organization/School/Campus`, `rbac.py`, `routers/context.py`, `AuditLog`, `NotificationHistory`, `routers/site.py` (CMS/branding), 4-locale i18n, dark mode, FastAPI auto-OpenAPI |
| | **Department** entity, **Feature flags**, **Global search** | ⬜ | no `Department`/`FeatureFlag` model; no global-search endpoint found |
| **2 SIS** | Profiles, guardians, admissions, enrollment, transfers, alumni, photos, QR/RFID | 🟡 | `routers/students.py`, `student_lifecycle.py`, `operations.py` (admissions), `ProfileAvatar`; QR/RFID exist on transport boarding |
| | Medical records, emergency contacts, student-ID/QR generation as first-class | ⬜/🟡 | partial; numref exists, no dedicated medical/emergency models confirmed |
| **3 Academic** | Years, terms, classes, subjects, programs, timetable, attendance, grades, report cards | ✅/🟡 | `routers/education.py`, `grades.py`, `attendance.py`, `pedagogy.py`; timetable conflict engine exists; GPA automation 🟡 |
| **4 AI Learning** | AI infra, 41 agents, chat, credits, automation | 🟡 | `ai_service.py`, `routers/chat.py`, `services/ai_agents.py` (41 agents), `ai_credits.py`, `ai_automation.py`; dedicated tutor/quiz/exam **generators** as product surfaces 🟡 |
| **5 Finance** | Fees, payments, invoices, reports, refunds | ✅/🟡 | `routers/finance.py`, `services/commerce.py` |
| **6 Transport (TMS)** | Fleet, drivers, vehicles, routes, stops(GPS), assignments, boarding, GPS positions, AI optimizer, billing→Finance, notifications | ✅ (foundation) | `routers/transport.py` (built this session); migrations 0035–0037 |
| | Real-time GPS push, native parent/driver apps, facial-recognition boarding, ETA prediction | ⬜ (roadmap) | documented in `transport/AGENTS.md` |
| **7 Communication** | Email/SMS/push, internal/parent/teacher messaging, announcements | 🟡 | `NotificationHistory`, `services/notification_service.py`, `automation.record_notification`, `finance/sms` |
| | WhatsApp, voice calls, video meetings, emergency broadcast | ⬜ | not implemented |
| **8 HR** | Staff/teachers, payroll, employment | 🟡 | `routers/teachers.py`, `employment.py`, payroll in `operations.py` |
| | Recruitment, contracts, leave, appraisals, training/certifications | ⬜/🟡 | partial |
| **9 Analytics & BI** | Dashboards, KPIs, AI insights, exports | 🟡 | `routers/dashboard.py`, `enterprise.py`, AI reports |
| | Predictive analytics, custom dashboards, drill-down, Excel/PDF/CSV export | ⬜/🟡 | partial |
| **10 Extensibility** | REST + OpenAPI | ✅ | FastAPI |
| | GraphQL, webhooks (inbound + outbound retry), plugin framework, marketplace, SDK, OAuth2/OIDC IdP, LMS/ERP integrations | ⬜ | not implemented |

### Payment infrastructure (mandatory cross-cutting) — already substantial

| Requirement | State | Evidence |
|---|---|---|
| Centralized Payment Service (single entry) | ✅ | `services/payment_gateway.py::create_checkout_session(provider, …)` |
| Stripe / CinetPay / Djamo gateways | ✅ | `_stripe_checkout`, `_cinetpay_checkout`, `_djamo_checkout` (env-gated; return `pending_configuration` when unset) |
| Cash payment recording (cashier) | 🟡 | finance payment records exist; cashier/receipt fields need confirming against the cash spec |
| Per-institution enable/disable, multi-currency | 🟡 | currency handling present (XOF/FCFA); per-institution gateway toggle to verify |
| Webhooks, idempotency, reconciliation, retries, refunds, receipts | 🟡/⬜ | partial — **must be audited & hardened**, not rebuilt |
| Item types (tuition/transport/exam/canteen/…) | ✅ | `commerce.py` `SCHOOL_ITEM_TYPES` / `PLATFORM_ITEM_TYPES` |

**Implication:** the payment loop is *extend + verify + harden*, never *rebuild*.

## 3. Acceptance criteria (per loop — verbatim from the supplied spec)

The per-loop "Acceptance Criteria" and the **Global** and **Payment** acceptance
criteria from the user's Master Feature Definition are adopted **unchanged** as
the definition-of-done. They are reproduced in `GOAL.md` against each slice so
each run has a measurable exit.

## 4. Global non-negotiables (adopted)

Production-ready, multi-tenant, enterprise RBAC, OpenAPI, type-safe FE/BE,
responsive, dark/light, **WCAG 2.1 AA**, i18n, audit logging, pluggable AI
providers, modular services, full automated tests (unit/integration/e2e), CI/CD,
Docker/K8s, horizontal scale, HA/fault-tolerance, security-by-design (OWASP Top
10, encryption in transit/at rest, rate limiting, secrets mgmt), perf (<300 ms
standard API, 100k+ users/tenant, millions of records), monitoring/logging/
tracing/alerting, **zero data duplication**.

## 5. Open decisions — NOT invented (must be supplied before the relevant loop)

1. **Real payment credentials & accounts** (Stripe/CinetPay/Djamo keys, webhook
   secrets) — required to make integrations "fully operational" per acceptance
   criteria. Not present; will stay `pending_configuration`.
2. **Currencies & institutions** that each gateway is enabled for.
3. **Infra/runtime ownership** (K8s cluster, HA topology, tracing/APM stack) —
   the perf/scale/HA criteria are infra-level and need an environment + owner.
4. **Native mobile apps** (parent/driver) — separate codebases/app-store
   accounts; in-scope as APIs only unless a mobile stack is chosen.
5. **Facial-recognition boarding, real-time GPS push (MQTT/WebSocket), ETA
   prediction** — need a vendor/broker + privacy/consent policy.
6. **WhatsApp/voice/video** providers (e.g. Twilio/Meta) — accounts + approval.
7. **GraphQL / plugin marketplace / SDK** scope — large surfaces; confirm before
   committing.
8. **Data-residency / encryption-at-rest** target (DB-level vs app-level) and
   secrets manager choice.

## 6. Out of scope for in-sandbox execution / authority-gated

- Anything spending money, contacting real users, or hitting live payment/comms
  providers.
- Production deploys, K8s manifests applied to a live cluster, DNS/secrets.
- Building/publishing native mobile apps or third-party marketplace listings.

## 7. Environment readiness (tools)

| Capability | Ready? | Note |
|---|---|---|
| Backend build/tests (`pytest`, `alembic`) | ✅ | 121 tests pass; migrations run |
| Frontend build/lint/e2e (`npm`, Playwright) | ⬜ | **no `node_modules` in sandbox** — frontend verified by inspection only |
| Real payment/comms provider calls | ⬜ | no credentials; integrations stay configurable/mock |
| Docker/K8s/monitoring stack | ⬜ | not provisioned here |
| DOX discipline (`*.md` sidecars, `AGENTS.md`) | ✅ | enforced each change |

## 8. Overall Goal Forge verdict

**READY TO EXECUTE** for software-buildable, sandbox-verifiable slices that
extend existing modules (backend tested via pytest; frontend by inspection).
**NOT READY** for: live payment/comms operability, infra/scale/HA/tracing,
native mobile, facial recognition, and any authority- or credential-gated item —
these need the §5 decisions and explicit grants before their loops can claim
their acceptance criteria. See `GOAL.md` for the ordered plan and first slice.
