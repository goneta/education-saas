# test_parent_digest.py — Tests for the weekly parent digest (automation C)

## Coverage

- Digest compiles grades (average /20 in the message), absences and outstanding
  fees into one `parent.digest` notification addressed to the linked parent.
- Threshold alerts: average below the bar → `parent.alert.average`; absences at
  the count → `parent.alert.absences` (both alongside the digest).
- Idempotence: a second run within the window sends nothing (`skipped_cooldown`).
- Language: parents with `UserPreference.language` en/sw receive their locale's
  subject ("Weekly digest…", "Muhtasari wa wiki…").
- Tenant scope: running for school A ignores school B's families; endpoint RBAC
  (teacher → 403 on `/automations/parent-digest/run`); history endpoint works.

## Pattern

In-memory SQLite (StaticPool) + direct router/service calls; fixtures build the
full grade chain (AcademicYear → Term → Class → Subject → Assessment → Grade)
and the attendance chain (Class → Subject → Timetable → Attendance).
