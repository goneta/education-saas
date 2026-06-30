# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/operations/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

- Record tables use the shared universal `TableFilter` / `useTableFilter` (column selector + debounced accent/case-insensitive search-as-you-type, persisted per `storageKey`); reuse it for any new collection rather than bespoke search inputs.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
- The transport section was removed from this page and promoted to the dedicated Smart Transport module (`/dashboard/transport`).
- i18n: localized via tx()/PRODUCT_COPY (FR/EN/ES/SW). Section labels, field placeholders and table columns are routed through key maps (SECTION_KEY / COLUMN_KEY / labelKey); prompts and chrome localized.
