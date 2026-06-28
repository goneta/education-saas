# table-filter.tsx

## Purpose

- The universal, reusable table/list/grid filter shared across the whole app: a column selector + a debounced, accent- and case-insensitive search-as-you-type field (no search button).
- `useTableFilter(rows, columns, options?)` owns the column/query state, debounces input, optionally persists the selection per `storageKey` in sessionStorage (preserved across navigation), and returns `{ filtered, controls, activeQuery }`.
- `<TableFilter {...controls} />` renders the controlled UI. Column labels/accessors are supplied by the caller and generated from the dataset.

## Maintenance Notes

- Presentation-only over a client-held array, so it composes with existing pagination/sorting/exports/bulk actions (it just narrows the array they operate on). For server-paged datasets, drive `controls.query` into the API request instead (same component, controlled).
- All text/accent folding goes through `lib/normalize`; chrome strings live in the `filters` i18n namespace. Reuse this component instead of per-page search inputs.
- Canonical usage wired in `app/[locale]/dashboard/teachers/page.tsx`.
