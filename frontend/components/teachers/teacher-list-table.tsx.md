# teacher-list-table.tsx

## Source File

- `frontend/components/teachers/teacher-list-table.tsx`

## Purpose

- Displays teacher loading, error, empty, filtered-list, and row-action states.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- An API error takes precedence over the empty-list state so production communication failures remain visible.
- The primary teacher list opts out of global auto-collapse, exposes the loaded count, and uses dark-compatible table/action surfaces.
- Teacher identity cells use the shared protected profile avatar and upload control.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
- i18n: uses the shared `lists` namespace (FR/EN/ES/SW) — no hardcoded UI strings (titles, columns, buttons, empty/loading states, dialog).
