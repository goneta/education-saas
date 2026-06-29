# TeducAI — GOAL.md (Goal Forge execution plan)

> Companion to `SPEC.md`. Produced by the Goal Forge loop. Defines ordered work,
> per-slice definition-of-done (DoD), required authority, and stopping
> conditions. **Approval to run a slice is per-slice and explicit** — this file
> does not authorize execution.

## Execution principles

1. **Extend, never duplicate.** Every loop builds on existing master data
   (`Organization/School/Campus`, `User/RBAC`, `ai_service`, `payment_gateway`,
   `NotificationHistory`). New code reads/writes shared models, never forks them.
2. **Vertical slices.** Each slice = models + migration + tenant-scoped + RBAC-
   gated endpoints + tests + frontend (where buildable) + DOX sidecars + one
   commit. This mirrors how the Transport module was just delivered.
3. **Per-step verification** (matches our proven workflow): `alembic upgrade
   head` + `pytest backend` must stay green; frontend verified by inspection
   (no `node_modules` in sandbox); DOX sweep before each commit.
4. **Stop on the supplied acceptance criteria**, or mark a slice **blocked /
   not-ready** (never fake an infra/credential criterion as met).

## Dependency-ordered roadmap

```
Payment Service hardening (cross-cutting)  ← unblocks every financial loop
        │
Loop 1 Core gaps (Department, Feature flags, Global search)
        │
Loop 2 SIS gaps ── Loop 3 Academic gaps
        │                  │
Loop 5 Finance ◄───────────┘  (consumes Payment Service)
        │
Loop 6 Transport hardening (real-time/mobile = NOT READY)
Loop 7 Communication (email/SMS ✅; WhatsApp/voice/video = NOT READY)
Loop 8 HR · Loop 9 Analytics/BI  (software-buildable)
Loop 10 Extensibility (GraphQL/webhooks buildable; marketplace/SDK = decide)
Loop 4 AI Learning generators (buildable on existing ai_service)
```

## Per-loop definition-of-done (adopts the spec's acceptance criteria)

Each loop is "done" only when **its** acceptance criteria from `SPEC.md` §3 plus
the Global non-negotiables (§4) plus, for any billable feature, the Payment
acceptance criteria are satisfied and verified. Infra/scale/HA/perf criteria are
tracked but require the §5 decisions + an environment to claim.

## Progress log

- **Slice 0 — ✅ DONE** (centralized Payment Service hardening): added
  `services/payment_service.py` (idempotent `apply_school_payment` + per-institution
  `enabled_providers`) and `routers/payments.py` (`/providers`, signed idempotent
  `/webhook/{provider}`, manager-gated `/{reference}/verify`, `/{reference}`).
  School payments now confirm exactly once and update the owning `StudentInvoice`
  (no double-credit on webhook replay). 6 new tests; 127 backend tests pass.
  **Still NOT READY (credential-gated):** live provider operability, Stripe HMAC
  body-signature, Apple/Google Pay device flows — `_verify_signature` is the plug
  point once real secrets exist.

- **Slice 1 — ✅ DONE** (Loop 1 Core gaps): `Department` + `FeatureFlag` models (migration 0038), `routers/platform.py` (departments CRUD, feature flags with `feature_enabled` fallback helper, tenant-scoped global search). 5 new tests; 132 backend tests pass.

- **Slice 2 — ✅ DONE** (Loop 2 SIS gaps): `StudentGuardian`, `StudentEmergencyContact`, `StudentMedicalRecord` (migration 0039), `routers/sis.py` (guardians/emergency CRUD, restricted medical upsert). 4 new tests; 136 backend tests pass.

- **Slice 3 — ✅ DONE** (Loop 3 Academic gap): automatic weighted GPA — `services/academics.py` + `/academics/students/{id}/gpa` (no migration; computes over existing grades). 3 new tests; 139 backend tests pass.

- **Slice 4 — ✅ DONE** (Loop 7 Communication): `Announcement` model (migration 0040) + `/communication` (create/list/publish-with-fan-out, emergency flag). WhatsApp/voice/video adapters NOT READY (provider accounts). 3 new tests.

- **Slice 5 — ✅ DONE** (Loop 8 HR): leave self-service + approval workflow on the EXISTING `LeaveRequest` model (no duplicate table) — `/hr/leave-requests` (own/all scoping) + `/decide` with notification. 3 new tests; 145 backend tests pass. Recruitment/contracts/appraisals/payroll-integration remain.

- **Slice 6 — ✅ DONE** (Loop 9 Analytics): `/analytics/export/{dataset}` tenant-scoped CSV + `/analytics/insights` AI narrative over KPIs. 3 new tests. PDF/Excel + predictive analytics remain roadmap.

## Recommended FIRST runnable slice

**Slice 0 — Centralized Payment Service: audit & harden** (highest leverage,
fully sandbox-verifiable, unblocks Loops 5/6/8/10).

- **Why first:** payment is mandatory cross-cutting and already substantially
  built; every financial loop depends on it. Hardening it now prevents each
  later loop from re-deriving payment logic (zero-duplication).
- **Scope (extend `services/payment_gateway.py` + `commerce.py` + finance):**
  - Idempotency keys on payment creation (prevent duplicate transactions).
  - Inbound **webhook** handlers (Stripe/CinetPay/Djamo) that verify signatures
    and update the owning business record + emit an audit log.
  - **Cash payment** recording fields per spec (cashier id, campus, receipt no.,
    invoice ref, outstanding-balance calc, receipt generation, audit trail).
  - Per-institution gateway enable/disable + multi-currency config.
  - Automatic **receipt** generation + payment-history + reconciliation status.
  - Refund + failed-payment + partial/installment scaffolding where applicable.
- **DoD (from the Payment acceptance criteria):** duplicate payments prevented;
  webhooks processed securely; cash recordable; providers configurable per
  institution; receipts auto-generated; every payment audit-logged and updates
  its business module; **integrations remain `pending_configuration` without
  real keys** (operability criteria deferred, explicitly, to credential supply).
- **Verification:** `pytest backend` (new payment tests: idempotency, webhook
  signature path with mock payloads, cash receipt, reconciliation); migration
  green; DOX sidecars; commit.
- **NOT in this slice (NOT READY):** live provider operability (needs real keys),
  Apple/Google Pay device flows, production webhook endpoints.

## Authority required before specific work (NOT granted by this spec)

- **Live payment operability / "fully operational" criteria** → real credentials
  + webhook secrets + explicit go-live approval.
- **Comms (WhatsApp/voice/video), facial recognition, real-time GPS** → provider
  accounts + privacy/consent sign-off.
- **Infra (Docker/K8s/HA/tracing) and any production deploy** → environment
  ownership + deploy approval.
- **Pushing to `github main`** → continue per the standing session norm, but each
  *outward* action (deploy, send, charge) remains separately gated.

## Stopping conditions

- **Per slice:** acceptance criteria met and verified → commit; or blocked →
  record the blocker + the missing input from `SPEC.md` §5 and stop the slice.
- **Per loop:** all its acceptance criteria green (or remaining ones explicitly
  marked credential-/infra-gated).
- **Global:** the program is "done" only when every loop's criteria are met or
  consciously deferred with an owner — not a single-run outcome.

## Goal Forge exit

Planning files **complete**. Scope settled; current-state mapped; gaps and
authority needs flagged without invention; first slice defined with a measurable
DoD and verification. **Awaiting your go/no-go on Slice 0** (or your choice of a
different first slice). No implementation has been started.
