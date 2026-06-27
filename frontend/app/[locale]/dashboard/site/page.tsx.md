# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/site/page.tsx`

## Purpose

- Super Admin editor for the public Site TeducAI CMS: edits hero, partners, FAQ, testimonials, pricing note, SEO meta, and footer, then saves via `PUT /site/content`.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Loads current content from the public `GET /site/content`; saves require the authenticated Super Admin token.
- Access is restricted to `super_admin`; other roles see an access-reserved message.
- List sections (partners, FAQ, testimonials) use a generic add/remove editor; the page is light/dark mode compatible.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/site/page.tsx"; npm run build when routes/layouts change
