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
- Runtime collapsible sections keep independent persisted open/closed state per page and section; toggling one section must not open, close, or remove controls from another section, including nested sections.
- Section chevrons are rendered as small, borderless controls at the right edge of the section container and must not be injected into the title flow.
- The enhancer also normalizes common remaining English dashboard labels, add buttons, and empty-state messages into French when rendered.
- Existing table actions should remain consolidated into one standardized action column: print, view, download, edit, delete.
- Containers marked `data-teducai-collapsible="false"` are never auto-collapsed; `data-teducai-default-open="true"` starts an enhanced section open.
- Runtime-injected section, action, and download-menu elements include explicit dark-theme styles to avoid white-on-white content.
- Edit/delete icons are injected only when the row exposes a real corresponding action; unavailable synthetic actions are not shown.
- Shared promise-based confirmations are rendered here for dashboard modules and bulk deletion.
- Every enhanced table receives a reusable dark-compatible toolbar for global search, column sorting, page size/pagination, reset, and persisted Table/Card view.
- Placeholder, loading, and empty-state rows are excluded from result counts, selection controls, and standardized row actions.
- Help modals and drawers must load the standalone `/{locale}/help` route so dashboard sidebar, top bar, and AI agent panels are not embedded inside the help window.
- Contextual help routing maps Employment dashboards to the Employment help section.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
