# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/transport/tracking/page.tsx`

## Purpose

- GPS tracking & safety: latest position per vehicle (`/transport/positions/latest`), a manual position-injection form (simulator/GPS-bridge stand-in for `/transport/positions`), and the safety alerts feed (`/transport/safety/alerts` — students assigned but not boarded this morning).

## Maintenance Notes

- Polls on load/refresh (no WebSocket yet — real-time push is roadmap). Position ingest requires a manager role server-side; a real device integration would use a service account.
