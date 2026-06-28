# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/transport/routes/page.tsx`

## Purpose

- Route management: list + create + delete against `/transport/routes`, linking each route to a driver and vehicle (loaded from `/transport/drivers` and `/transport/vehicles`) and carrying the monthly transport fee that integrates with Finance. Uses the shared universal `TableFilter`.

## Maintenance Notes

- `monthly_fee` is the transport fee surfaced in the dashboard revenue KPI. Driver/vehicle links are validated server-side to stay within the tenant.
