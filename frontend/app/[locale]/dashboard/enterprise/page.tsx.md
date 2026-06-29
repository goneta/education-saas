# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/enterprise/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Endpoint list cards are laid out one per row (full width), not two-up, so each table has room for its columns and action icons across breakpoints.
- Enterprise record deletion uses the shared TeducAI confirmation dialog.

- Record tables use the shared universal `TableFilter` / `useTableFilter` (column selector + debounced accent/case-insensitive search-as-you-type, persisted per `storageKey`); reuse it for any new collection rather than bespoke search inputs.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
- `ListCard` filterColumns is derived inline (not `useMemo`): `keys` is recomputed each render from `rows`, so a manual memo can't be preserved by the React Compiler — let it auto-memoize.
