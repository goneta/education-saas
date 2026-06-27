# page.tsx

## Source File

- `frontend/app/[locale]/page.tsx`

## Purpose

- Public localized homepage for the TeducAI marketing site, including hero, feature cards, trust sections, and dashboard preview mockup.
- Hero copy, CTAs, partner chips, FAQ, testimonials, and SEO metadata are loaded server-side from the Site CMS via `getSiteContent` (`@/lib/site-content`); `generateMetadata` sets title/description from the CMS SEO fields. FAQ and testimonials sections render only when the Super Admin has added entries. Feature cards and trust highlights remain code-defined.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- The public home and hero surfaces inherit the persisted global theme and keep navigation, copy, cards, and calls to action readable in dark mode.
- Dark mode uses a true dark header/hero/features surface with white navigation and high-contrast feature text.
- Dashboard preview mockup intentionally keeps inner white cards light in dark mode so embedded chart labels stay readable.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
