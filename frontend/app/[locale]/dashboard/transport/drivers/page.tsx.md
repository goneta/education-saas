# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/transport/drivers/page.tsx`

## Purpose

- Driver master-data management: list + create + delete against `/transport/drivers`, with the shared universal `TableFilter` (column selector + debounced accent/case-insensitive search).

## Maintenance Notes

- Writes require a manager role server-side; the UI surfaces backend failures. Reuse `TableFilter` for any new column rather than bespoke search.
