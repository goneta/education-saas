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

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
