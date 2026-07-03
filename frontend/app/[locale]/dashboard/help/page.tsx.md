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
- HELP_SECTIONS documents `selfDocs` (4-locale): self-service document generation for students/parents with unique verifiable references.
- The automations help section now also covers the weekly parent digest + threshold alerts (purpose + a dedicated step, 4-locale).
- The automations help section now also covers absence follow-up and the anomaly brief (purpose + two dedicated steps, 4-locale).
- The automations help section now also covers the rentree wizard (preview-then-run step, 4-locale).
- HELP_SECTIONS documents `studyPlan` (4-locale): spaced revision planner + homework nudges.
- HELP_SECTIONS documents `remediation` (4-locale): AI practice sets for struggling students, credit-gated, idempotent per student.
- HELP_SECTIONS documents `explainGrade` (4-locale): AI walk-through of a grade with class context, credit-gated, self/linked-child only.
- HELP_SECTIONS documents `sequenceBuilder` (4-locale): term lesson sequence from real timetable hours, credit-gated, kept in notifications.
- The employment help section now covers the three recruiter automations (match reasons, screening questionnaire, saved-search agents) - French legacy-section style.
- The employment help section now also covers the job-seeker automations (CV refresh, gap analysis, AI cover letter) - French legacy-section style.
- The automations absence-followup step now documents the parent one-tap actions (justify from the bell, pay deep-link) - 4-locale.
