# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/grades/reports/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

- Search uses the shared universal `TableFilter` / `useTableFilter` (column selector + debounced accent/case-insensitive search-as-you-type, persisted per `storageKey`); reuse it on collection pages instead of bespoke search inputs.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
- i18n: localized via tx()/PRODUCT_COPY (FR/EN/ES/SW); no hardcoded visible strings.
- Lint: locale added to the filter-columns useMemo deps.
