# models.py

## Source File

- `backend/models.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- Defines the SQLAlchemy data model, including traceable cash fee payments, AI billing, persistent school subscriptions, soft-deleted users, RBAC, and school payment accounts.
- AI provider records include optional account labels, manually synced available credits, and last-sync timestamps; `PlatformAISettings` stores platform low-credit alert settings.
- Defines TeducAI Emploi models for student CVs, sharecodes, work history, detailed skills, academic credentials, certificates, recruiter profiles, subscription plans, AI credit balances, job offers, applications, matching metadata, interviews, notifications, and CV access logs.
- `UserRole.RECRUITER` is the primary role for newly registered recruiter accounts; SQLAlchemy persists this enum as the `RECRUITER` database label, and `RecruiterProfile` remains the authoritative recruiter-domain record.
- `SiteContent` is a singleton JSON document holding the editable public marketing-site content (hero, partners, FAQ, testimonials, pricing, SEO, footer) managed by the Super Admin; the public site falls back to code-level defaults when it is empty.
- `TeacherProfile` is the single global teacher identity (unique per user); `TeacherAssignment` records each school/model a teacher is actively engaged at, so one teacher can teach concurrently at several schools (mirrors `StudentEnrollment` for learners).
- `TimetableConstraintRule` stores admin-configurable scheduling constraints (rule_type + JSON parameters + severity, scoped by school/model) so no pedagogical rule is hard-coded; it is interpreted by `services/timetable_constraints.py`.
- `Campus`/`Building`/`Room`/`RoomEquipment` model schedulable facilities (multi-campus, room type/capacity/equipment); `Timetable.room_id` links a course to a `Room` (the legacy `room` string is kept for back-compat).
- `TimetableConfig` (working days + course/break/lunch slots), `SchoolHoliday` (non-working dates), and `SubjectRequirement` (weekly volume per subject/class/level) make the scheduling grid configurable; generation reads them via `services/timetable_config.py` instead of hard-coded days/slots.
- `TeacherAbsence` records absences for substitution/replanning; `Timetable.delivery_mode` supports hybrid courses (in_person/remote/hybrid).

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- User records persist an optional protected `profile_photo_url`; school records do not own user profile photos.
- Organizations own schools; schools activate global school models through assignment rows.
- Core academic, finance, AI usage, preference, and audit records carry assignment-level context while seeded references expose `is_system_default`.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
# Student lifecycle

`StudentGlobalProfile` is the unique learner identity. `StudentEnrollment` records each school, model, academic year, class, program, schedule, and concurrent-training context. Transfers, year locks, historical edit grants, import batches, and migration reports preserve cross-school history without sharing finance.

Grades, attendance, assignment submissions, internships, fees, invoices, registration documents, certificates, and AI usage can reference the precise enrollment.

# TeducAI Emploi

`StudentCV` belongs to either a `StudentGlobalProfile` or an external employment-only user. Public recruiter access goes through `sharecode`, `share_enabled`, privacy settings, payment restrictions, and access logs. Recruiter data lives in `RecruiterProfile`; offers, applications, notifications, matching summaries, subscriptions, company logo metadata, and interviews are scoped to that recruiter profile.
- Smart Transport master data: `TransportDriver`, `TransportVehicle`, and `TransportRoute.driver_id/vehicle_id/capacity` links (single source of truth for the `/transport` module).
- `TransportStop`: first-class bus stops (route_id, sequence, lat/lng, geofence radius, ETA) replacing the legacy `TransportRoute.stops` JSON.
- GPS/ops layer: `TransportVehiclePosition` (GPS samples), `TransportBoardingEvent` (boarding attendance), `TransportIncident`, `TransportFuelLog`.
- Core Platform: `Department` (school/campus org unit) and `FeatureFlag` (per-institution toggle over a NULL-school platform default).
