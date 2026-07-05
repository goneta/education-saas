# registry.ts — Locale-aware docs content resolver

English (`content.ts`) is the source of truth and the fallback; per-locale
modules (`content.<locale>.ts`) are merged OVER the English maps so an untranslated
page falls back to English instead of 404-ing (same graceful-fallback pattern as
the in-app Help Center).

Exports:
- `getDocPages(locale)` / `getDocPage(locale, slug)` — pages with per-page EN fallback.
- `getDocGroups(locale)` — sidebar groups (localized titles + item labels); tab keys stay English.
- `getTabLabel(tab, locale)` — localized display label for a tab identity key.
- `docsUi(key, locale)` — localized chrome string (search, copyPage, onThisPage, …) with EN fallback.

Registered locales: `fr` (full). `es`/`sw` fall back to English until their
`content.<locale>.ts` modules are added to the `*_BY_LOCALE` maps.

All docs components (docs-app, docs-content, docs-sidebar, docs-header) resolve
content and chrome through this module — none import `content.ts` maps directly
anymore (except `DOC_TABS`/`DOC_GROUPS` for locale-independent tab identity/slug
lookup and `DEFAULT_SLUG` in the route).
