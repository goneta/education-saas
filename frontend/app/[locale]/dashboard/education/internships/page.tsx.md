# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/education/internships/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Follow-up/logbook and document sections are laid out one per row (full width), not two-up, so their tables and action icons have room across breakpoints.

- Record tables use the shared universal `TableFilter` / `useTableFilter` (column selector + debounced accent/case-insensitive search-as-you-type, persisted per `storageKey`); reuse it for any new collection rather than bespoke search inputs.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
