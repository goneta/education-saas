# docs-sidebar.tsx

## Purpose
- Left sidebar: search, the nav tree filtered by the active tab, and an account switcher pinned at the bottom.
- Cmd/Ctrl+K focuses the search input (only when this sidebar instance is visible; checked via offsetParent).
- Locale-aware: content, group/tab labels and chrome strings resolve through lib/docs/registry.ts (getDocPage/getDocGroups/getTabLabel/docsUi), so selecting Français renders the full French documentation (body + sidebar + chrome). Tab identity keys stay English.
