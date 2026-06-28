# transport.py

## Source File

- `backend/routers/transport.py`

## Purpose

- The Smart Transport module API (`/transport`), promoted out of the generic Operations table into a first-class module. Owns normalized master data — drivers, vehicles, routes — plus student transport assignments and a KPI dashboard.

## Local Contracts

- Every endpoint is tenant-scoped via `_school_id(current_user)`; reads are open to any authenticated user in the school, writes require a manager role (`MANAGER_ROLES`).
- Assignments reference real `StudentProfile` records; the student's school is resolved through the linked `User` and must match the caller's tenant (no cross-school leakage).
- Routes carry `monthly_fee` (flows into Finance) and optional `driver_id`/`vehicle_id` links validated to stay within the tenant.
- `TransportRoute` is the same table the legacy `/operations/transport` endpoints used, so transport data is a single source of truth across both.

## Roadmap (not yet implemented)

- GPS tracking (MQTT→Redis→WebSocket), AI route optimization, boarding attendance (QR/RFID/face), parent/driver/student mobile apps, notification fan-out, and the AI safety monitoring described in the Smart Transport architecture build on this foundation. See `frontend/app/[locale]/dashboard/transport/AGENTS.md` for the full roadmap.

## Verification

- `python -m py_compile backend/routers/transport.py`
- `python -m pytest backend/test_transport.py`
