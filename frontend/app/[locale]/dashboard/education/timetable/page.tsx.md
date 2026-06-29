# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/education/timetable/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Timetable entry deletion uses the shared TeducAI confirmation dialog.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
- Renders `TimetableConstraintsPanel` (constraint engine UI: AI optimized generation, grid config, weekly hours, holidays, pedagogical rules, always-enforced constraints), passing the loaded subjects/teachers/classes.
