# content.ts

## Purpose
- Typed content for the TeducAI Platform Docs site. `DOC_GROUPS` is the sidebar nav tree (each group tagged with a top tab); `DOC_PAGES` maps slug -> page (title, description, breadcrumb, `DocBlock[]`). Feature pages are sourced from the three feature docx (AI Timetable Engine, Cash payments & AI credits, Smart Transport); the rest are written from the implemented modules.
## Maintenance Notes
- Add a page by adding a `DOC_PAGES` entry and listing its slug under a `DOC_GROUPS` item. Inline text supports `code`, **bold** and [label](/path) (internal links auto-prefixed with the locale).
- api-webhooks page documents the real partner API (X-API-Key auth, /api/v1 endpoints table, webhook event types, delivery/retry semantics); the timetable-engine integration callout corrected (transport pickup recalculation marked roadmap, not shipped).
- New "Automations" Features group: `automations` (the full 19-feature suite by user group, shared principles - real data, idempotent, credit-gated, never faked; cron endpoints; AI provider order OpenAI+Anthropic primary / OpenRouter+Manus+Genspark fallback) and `esignature` (self-service documents + in-house cryptographic e-signature with the eIDAS scope note).
- English is now the source-of-truth/fallback for a locale-aware system: French lives in `content.fr.ts` and is resolved via `registry.ts` (per-page EN fallback). The docs language dropdown now translates the whole page body, not just the URL locale.
- New "Homework & exercises" page (`assignments`) under Academic management: the full module (AI generation + corrigé, online/paper, submissions, manual+AI grading, gradebook bridge, stats, access rules) with a foundation-vs-roadmap callout. French page in content.fr.ts.
