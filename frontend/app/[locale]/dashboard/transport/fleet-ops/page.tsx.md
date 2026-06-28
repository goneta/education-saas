# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/transport/fleet-ops/page.tsx`

## Purpose

- Fleet operations: report/list/delete safety & operational incidents (`/transport/incidents`) and log fuel consumption (`/transport/fuel-logs`). Both feed the dashboard KPIs (open incidents, fuel cost).

## Maintenance Notes

- Writes require a manager role server-side; vehicle links validated to the tenant.
