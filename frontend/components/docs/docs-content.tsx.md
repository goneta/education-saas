# docs-content.tsx

## Purpose
- Center column: breadcrumb, H1 + Copy-page (markdown to clipboard), intro, and the rendered `DocBlocks`.
- Locale-aware: content, group/tab labels and chrome strings resolve through lib/docs/registry.ts (getDocPage/getDocGroups/getTabLabel/docsUi), so selecting Français renders the full French documentation (body + sidebar + chrome). Tab identity keys stay English.
