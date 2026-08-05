# missing-dependency.tsx
## Source File
- `frontend/components/ui/missing-dependency.tsx`
## Purpose
- The app-wide uniform behavior when a creation form depends on data that does
  not exist yet: `MissingDependency` (amber callout: explicit French message
  naming the missing data + quick-create buttons that navigate to the creation
  page), `RequireOptions` (wraps a DB-fed select: skeleton while loading, the
  callout when empty, the field otherwise) and `missingRequired(lists)` (one-line
  submit blocking: disable the submit button while a required list is
  loaded-and-empty).
## Local Contracts
- EVERY new creation form with DB-fed dropdowns must use these instead of
  rendering an empty select. Wired so far: add-student modal, classes (level),
  rooms (building), timetable entry (class/subject/teacher), assignments
  (class/subject), create-assessment modal (class/subject/term).
## Verification
- Type-check by inspection (no node_modules in sandbox).
