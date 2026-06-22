# Purpose

Adds the global student lifecycle schema, enrollment-scoped data links, transfer workflow, academic-year locks, temporary historical edit grants, import batches, and a migration report.

# Data migration

- Creates one deterministic global profile per legacy student profile.
- Creates one current enrollment per legacy student using its existing school, model assignment, academic year, and class.
- Creates a default academic year only when the legacy context has none.
- Backfills enrollment IDs into grades, attendance, submissions, internships, fees, invoices, registration documents, and certificates.
- Records counts and warnings in `student_lifecycle_migration_reports`.
