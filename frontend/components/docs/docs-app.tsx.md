# docs-app.tsx

## Purpose
- Client orchestrator for the docs site: header + left sidebar (desktop + mobile drawer) + center content + right scroll-spy TOC + floating Ask button. Derives the active top tab from the current slug.
- Mobile: a floating 'On this page' button (bottom-left, xl:hidden) opens a bottom-sheet TOC of the page's h2/h3 anchors; body scroll locks while the drawer or TOC sheet is open.
- Locale-aware: content, group/tab labels and chrome strings resolve through lib/docs/registry.ts (getDocPage/getDocGroups/getTabLabel/docsUi), so selecting Français renders the full French documentation (body + sidebar + chrome). Tab identity keys stay English.
