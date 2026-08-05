# module-page.tsx
## Source File
- `frontend/components/school-life/module-page.tsx`
## Purpose
- Generic config-driven CRUD page powering the five Vie scolaire modules: ONE
  component provides list + server-side search, status/type filters, exact
  pagination, create/edit dialog, delete-with-confirm, CSV export (auth fetch →
  blob download) and print (`window.print`, chrome hidden via `print:hidden`).
  Each module page is just a `ModuleConfig` (slug, columns, fields, statuses).
- Field types: text/textarea/date/number/checkbox/select + SOURCE fields
  (student → /students via student_profile.id, class, subject, room →
  /facilities/rooms, reference → merged 🌐+🏫 `/reference-data/{category}`).
  Source fields are wrapped in `RequireOptions` (explicit missing-data message
  + quick-create button) and required empty sources disable submit via
  `missingRequired`. API errors flow through lib/api-errors (per-field +
  readable message — never "[object Object]").
## Local Contracts
- New Vie scolaire-style modules should be one backend `_register_module` call
  + one `ModuleConfig` page — no bespoke CRUD code.
## Verification
- Type-check by inspection (no node_modules in sandbox); backend contract in
  test_school_life.py.
