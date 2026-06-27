# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/education/timetable/engine/page.tsx`

## Purpose

- Admin UI for the configurable timetable engine: edit the scheduling grid (working days + slots), manage constraint rules, run the optimiser (compare scored candidates and apply one), and run what-if simulations.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Talks to `/education/timetables/{config,constraint-rules,constraint-rule-types,optimize,optimize/commit,simulate}` with the bearer token; rule types come from the backend so the UI never hard-codes them.
- Each section is laid out one per row (full width) per the admin-layout convention; dark-mode aware.
- Backend is the source of truth for validation (rule types, severities, JSON parameters); the UI surfaces backend error messages.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/education/timetable/engine/page.tsx"; npm run build when routes/layouts change
