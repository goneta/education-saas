# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/transport/vehicles/page.tsx`

## Purpose

- Fleet (vehicle) master-data management: list + create + delete against `/transport/vehicles` (type, registration, capacity, status), with the shared universal `TableFilter`.

## Maintenance Notes

- Capacity feeds the dashboard occupancy KPI. Writes require a manager role server-side.
