# page.tsx
## Source File
- `frontend/app/[locale]/dashboard/personnel/page.tsx`
## Purpose
- Personnel scolaire admin page (#7): create staff (name, email, phone, primary role, additional roles as chips, department, function, status) → `/personnel`; list with inline status change + deactivate. Shows the generated temporary password once. i18n `personnel` namespace. In the Gestion sidebar section.
- Uses the shared `TableFilter`/`useTableFilter` (storageKey "personnel") for column-scoped, debounced, accent-insensitive search over the list.
