# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/help/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.
- Provides the dashboard help center, including AI cash/free validation, school credit allocation and revocation, provider fallback, wallet limits, separated payments, mobile UX, documents, internships, settings, finance, and core workflows.
- Exports `HelpContent` so standalone help routes, dashboard page mode, modal mode, and drawer mode share the same contextual sections.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Include a dedicated Employment help section for student CVs, ShareCodes, recruiters, payment restrictions, offers, matching, and AI credits.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/help/page.tsx"`
- `cmd.exe /c "cd frontend&& set NODE_OPTIONS=--max-old-space-size=4096&& npm run build"` when help routing or page structure changes.
- HELP_SECTIONS now documents the new modules (ids `levels`, `facilities`, `personnel`, `payroll`) — purpose, steps, fields, expected result. Deep-linked via `?section=<id>`.
- HELP_SECTIONS also documents `leave` and `announcements` (#1).
- i18n (#2): the page chrome (title, subtitle, search, help-mode options, Sections nav, standard-form-cycle, Objectif/Etapes/result labels, field-table headers) uses the help namespace (FR/EN/ES/SW). The per-section HELP_SECTIONS content (purpose/steps/fields) stays French - full content translation is a separate effort.
- Help CONTENT is now locale-aware: a `loc(value, locale)` resolver accepts either a plain French string (legacy fallback) or a `{fr,en,es,sw}` object. The 6 new-module sections (levels, facilities, personnel, payroll, leave, announcements) are fully translated; the remaining legacy sections stay French until translated (resolver falls back).
- HELP_SECTIONS documents `automations` (4-locale) with context-aware routing.
