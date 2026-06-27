# site-content.ts

## Purpose

- Server-side helper that reads the public Site CMS content (`GET /site/content`) for the marketing/landing pages.
- Provides typed `SiteContent` interfaces and `DEFAULT_SITE_CONTENT` fallbacks.

## Local Contracts

- Fetches the backend through `BACKEND_INTERNAL_URL` (defaults to `http://127.0.0.1:8000`) because relative proxy URLs are not resolvable during server rendering.
- Always returns a fully-populated `SiteContent`: on any failure or partial payload it merges over `DEFAULT_SITE_CONTENT` so the landing page never breaks.
- Uses `next: { revalidate: 60 }` so Super Admin edits propagate without a redeploy.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint lib/site-content.ts"`
