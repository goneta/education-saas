# content.ts

## Purpose
- Typed content for the TeducAI Platform Docs site. `DOC_GROUPS` is the sidebar nav tree (each group tagged with a top tab); `DOC_PAGES` maps slug -> page (title, description, breadcrumb, `DocBlock[]`). Feature pages are sourced from the three feature docx (AI Timetable Engine, Cash payments & AI credits, Smart Transport); the rest are written from the implemented modules.
## Maintenance Notes
- Add a page by adding a `DOC_PAGES` entry and listing its slug under a `DOC_GROUPS` item. Inline text supports `code`, **bold** and [label](/path) (internal links auto-prefixed with the locale).
