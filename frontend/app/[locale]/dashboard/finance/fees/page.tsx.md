# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/finance/fees/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.
- Manages school fees and traceable payments, including cash, Mobile Money, bank, Stripe, Djamo, and CinetPay references and notes.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Fee deletion uses the shared TeducAI confirmation dialog before calling the audited API.

- Search uses the shared universal `TableFilter` / `useTableFilter` (column selector + debounced accent/case-insensitive search-as-you-type, persisted per `storageKey`); reuse it on collection pages instead of bespoke search inputs.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
