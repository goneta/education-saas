# page.tsx
## Source File
- `frontend/app/[locale]/dashboard/levels/page.tsx`
## Purpose
- Super-Admin school-levels referential admin page (`/levels` CRUD + activate/deactivate). Fully i18n via the `schoolLevels` namespace.
## Maintenance Notes
- In the System sidebar section. Writes require super-admin (backend 403 otherwise). Schools consume this list when creating classes / on the student form (level→class cascade).
- Uses the shared `TableFilter`/`useTableFilter` (storageKey "levels") for column-scoped, debounced, accent-insensitive search over the list.
