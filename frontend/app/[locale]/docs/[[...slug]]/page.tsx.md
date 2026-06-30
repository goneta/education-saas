# page.tsx (docs)

## Purpose
- Optional catch-all route for `/{locale}/docs` and `/{locale}/docs/{slug}`. Server component: awaits params, normalizes locale, renders `DocsApp` with the slug (defaults to `intro`).
