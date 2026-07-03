# schemas.py

## Source File

- `backend/schemas.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Exposes API schemas for schools, users, AI billing, and other modules, including username, system-account flags, account type, and dashboard destination hints in user responses.
- `AIProviderResponse` includes `balance_api_supported`, indicating whether the provider's balance can be auto-synced from its API.
- `StudentProfileResponse` overrides `date_of_birth`, `gender`, and `parent_email` as optional/plain on read so admission/import-created profiles (which may lack them, or hold a malformed email) do not 500 the roster; creation schemas keep these required/validated.
- `TimetableConstraintRule*` schemas describe the configurable scheduling rules (rule_type, JSON parameters, severity, scope); the router validates `rule_type` against the engine's supported list.
- `Campus*`/`Building*`/`Room*`/`RoomEquipmentItem` schemas back the facilities API; room create/update embed the equipment list (replaced wholesale on update).
- `TimetableConfig*`/`TimetableSlot`/`SchoolHoliday*`/`SubjectRequirement*` schemas back the configurable scheduling grid (days/slots, holidays, weekly volume).
- `TimetableOptimizeRequest`/`TimetableOptimizeCommit` back the optimiser preview/commit endpoints; `TimetableSimulateRequest` backs the what-if simulation endpoint.
- `TeacherAbsence*`/`SubstitutionApply` back the absence recording and substitute-assignment endpoints.
- Defines Pydantic API contracts for school settings, cash fee payments, AI providers, wallets, targeted credit packs, manual cash/free credit validation, school allocations, platform payments, and school payments.
- AI provider contracts include account labels and available provider credits; platform monitoring contracts expose provider totals, sold/allocated credits, remaining platform credits, wallet balances, threshold settings, and low-credit alert state.
- AI credit purchase contracts carry target context, provider, optional Mobile Money network, redirect URLs, manual-validation notes, checkout URL, and provider status.
- Employment job offer responses expose optional recruiter/company logo URLs returned by the employment router.
- Defines persistent subscription-change/response contracts and exposes managed-user phone/deletion state.
- User, student, and teacher responses expose the optional protected profile-photo endpoint.
- Context contracts cover active assignment/year changes, school-model activation, non-destructive deactivation, AI enablement, and model-level limits.
- Organization owners can create additional schools with a selected set of model codes.
- TeducAI Emploi contracts cover student CV updates, detailed skills, academic credentials, certificates, work history technologies, sharecode lookup, external student registration, recruiter registration, recruiter profile/subscription/AI-credit updates, advanced job offers, applications with AI match scores, notifications, and interviews.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
# Student lifecycle

The schema catalog includes enrollment, transfer, academic-year closure, temporary historical edit grant, and transactional import payloads. These contracts preserve the existing student API while exposing the global student journey separately.

# Multi-school teaching

`TeacherAssignmentCreate` / `TeacherAssignmentResponse` describe a teacher's engagement at one school/model. They back the multi-school teaching endpoints and do not alter the existing `TeacherResponse` contract.
- Smart Transport: `TransportDriver*`, `TransportVehicle*` schemas and `driver_id/vehicle_id/capacity` on `TransportRouteCreate`.
- `TransportStop*` schemas for bus-stop CRUD.
- `TransportPosition*`, `TransportBoarding*`, `TransportIncident*`, `TransportFuelLog*` schemas.
- `SchoolPaymentWebhook` for centralized school-payment confirmation.
- `Department*` and `FeatureFlag*` schemas (Core Platform Slice 1).
- `Guardian*`, `EmergencyContact*`, `MedicalRecord*` schemas (SIS Slice 2).
- `Announcement*` schemas (Communication Slice 4).
- `LeaveSelfRequestCreate` + `LeaveDecision` for HR self-service leave (reuses the existing `LeaveRequest`/`LeaveRequestResponse`).
- `WebhookEndpoint*`, `ApiKey*` schemas (Extensibility Slice 7).
- `UserResponse.email` is tolerant `Optional[str]` on read (a stored email strict `EmailStr` rejects must not 500 a list/response); `UserBase`/`UserCreate` keep `EmailStr` for input. Fixes the Teachers/`/auth/me` 500.
- `SchoolResponse.email` is tolerant `Optional[str]` on read (nested in `UserResponse.school`, returned by teachers/students lists); a stored school email strict EmailStr rejects must not 500 the list. Input schemas keep EmailStr.
- `SchoolLevel*` schemas (#3 levels referential).
- `Building` gains `description`; `BuildingUpdate` added (#5).
- `Staff*` schemas (#7 Personnel scolaire); response email tolerant `Optional[str]`.
- `SalaryProfile*`, `Payslip*` schemas (#7 Payroll); response email tolerant.
- `StaffAssignment*` schemas (#3 personnel establishment history over `SchoolMembership`).
- `WebhookDeliveryResponse` + minimal `Public*` DTOs for the partner API v1.
- Security: AdmissionEnrollmentCreate.password no longer has a baked-in default; omitted -> server generates a strong credential returned once.
- `FeeReminderRunResult` / `FeeReminderResponse` (automation A).
