# transport.py

## Source File

- `backend/routers/transport.py`

## Purpose

- The Smart Transport module API (`/transport`), promoted out of the generic Operations table into a first-class module. Owns normalized master data — drivers, vehicles, routes — plus student transport assignments and a KPI dashboard.

## Local Contracts

- Every endpoint is tenant-scoped via `_school_id(current_user)`; reads are open to any authenticated user in the school, writes require a manager role (`MANAGER_ROLES`).
- Assignments reference real `StudentProfile` records; the student's school is resolved through the linked `User` and must match the caller's tenant (no cross-school leakage).
- Routes carry `monthly_fee` (flows into Finance) and optional `driver_id`/`vehicle_id` links validated to stay within the tenant.
- Bus stops (`/transport/stops`) are first-class GPS entities (lat/lng, geofence radius, sequence, ETA) scoped to a route within the tenant; `bus_stops` count is on the dashboard.
- `TransportRoute` is the same table the legacy `/operations/transport` endpoints used, so transport data is a single source of truth across both.

## Roadmap (not yet implemented)

- GPS tracking (MQTT→Redis→WebSocket), AI route optimization, boarding attendance (QR/RFID/face), parent/driver/student mobile apps, notification fan-out, and the AI safety monitoring described in the Smart Transport architecture build on this foundation. See `frontend/app/[locale]/dashboard/transport/AGENTS.md` for the full roadmap.

## Verification

- `python -m py_compile backend/routers/transport.py`
- `python -m pytest backend/test_transport.py`
- GPS positions (`/positions`, `/positions/latest`), boarding attendance (`/boarding`) + safety alerts (`/safety/alerts`, students not boarded this morning), incidents and fuel-logs CRUD; dashboard extended with fuel cost, open incidents and boardings today.
- AI route optimizer (`/routes/{id}/optimize`) via `ai_service` (local fallback when no provider); route-wide notifications (`/routes/{id}/notify`) and a per-boarding parent notification via the platform `NotificationHistory` (`automation.record_notification`).
