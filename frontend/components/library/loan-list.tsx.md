# loan-list.tsx

## Source File

- `frontend/components/library/loan-list.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It provides reusable UI behavior.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

- The list search uses the shared universal `TableFilter` / `useTableFilter` (column selector + debounced accent/case-insensitive search), so library lists behave like every other collection in the app.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
