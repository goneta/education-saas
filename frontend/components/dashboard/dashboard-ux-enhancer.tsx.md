# dashboard-ux-enhancer.tsx

## Source File

- `frontend/components/dashboard/dashboard-ux-enhancer.tsx`

## Purpose

- React/Next.js client component that adds reusable dashboard UX behavior after page render.
- It standardizes table/list row actions, mass actions, mobile table cards, contextual help access, French section-title normalization, and collapsible dashboard sections.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Collapsible sections are applied globally to section-like dashboard cards with headings and are collapsed by default so newly added sections follow the same interaction pattern.
- Existing table actions should remain consolidated into one standardized action column: print, view, download, edit, delete.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
