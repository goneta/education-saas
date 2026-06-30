# page.tsx
## Source File
- `frontend/app/[locale]/dashboard/buildings/page.tsx`
## Purpose
- Buildings management (#5): list/create/toggle/delete buildings (name, description, campus, state) via `/facilities/buildings`. Fully i18n (`facilities` namespace). In the Gestion sidebar section.
## Maintenance Notes
- Delete blocked (409) when the building has rooms. Admin-gated server-side.
- Uses the shared `TableFilter`/`useTableFilter` (storageKey "buildings") for column-scoped, debounced, accent-insensitive search over the list.
