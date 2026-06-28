# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/transport/stops/page.tsx`

## Purpose

- Bus-stop management: list + create + delete against `/transport/stops`, with GPS coordinates, sequence and scheduled-arrival ETA per stop, scoped to a route. Uses the shared universal `TableFilter`.

## Maintenance Notes

- Stops are first-class entities (replacing the legacy `TransportRoute.stops` JSON). They are the basis for live tracking and boarding attendance. Writes require a manager role server-side; route link validated to the tenant.
