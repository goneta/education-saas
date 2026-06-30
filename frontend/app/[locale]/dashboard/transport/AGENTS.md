# Smart Transport module

The school-transport domain, promoted out of the generic **Operations** table
into a first-class **Smart Transport** section (sidebar: Tableau de bord,
Chauffeurs, Véhicules, Trajets, Affectations élèves).

## Design principle — single source of truth

Smart Transport never duplicates core platform data; it consumes it:

| Core module | Transport consumption |
|---|---|
| Students (SIS) | Transport assignments link real `StudentProfile` records |
| Finance | Route `monthly_fee` becomes a transport fee category |
| Parents | (roadmap) boarding/delay notifications |
| Timetable | (roadmap) pickup-time recalculation on schedule change |
| Attendance | (roadmap) boarding attendance feeds school attendance |

## Implemented (this foundation)

- Backend `/transport` router (`backend/routers/transport.py`): drivers,
  vehicles, routes, student assignments (CRUD) + `/transport/dashboard` KPIs.
  Tenant-scoped; writes gated to manager roles; cross-school assignment blocked.
- Normalized master data: `TransportDriver`, `TransportVehicle`, route links
  (`driver_id`/`vehicle_id`/`capacity`), migration `20260628_0035`.
- Frontend module pages (this folder), each using the shared universal
  `TableFilter`. Sidebar "Smart Transport" section; transport removed from the
  Operations page. Route is school-context-guarded (`CONTEXT_REQUIRED_SEGMENTS`).
- **Finance billing**: `/transport/billing/generate` turns active assignments (route monthly_fee) into transport `Fee` rows in the single Finance ledger (idempotent per student+route+period); a "Générer les frais" action on the assignments page.
- **AI route optimizer** (`/transport/routes/{id}/optimize` via ai_service) and **transport notifications** (per-boarding parent notice + route-wide `/notify`) on the platform NotificationHistory. Multi-channel fan-out (SMS/WhatsApp push) and a real route-reorder algorithm remain roadmap.
- **GPS tracking (REST layer)**, **boarding attendance** + heuristic **AI safety alerts**, **incidents** and **fuel logs**, with extended dashboard KPIs (migration `20260628_0037`, pages: tracking, boarding, fleet-ops). Real-time WebSocket push and the boarded-bus-vs-school-attendance cross-check remain roadmap.
- **Bus stops** as first-class GPS entities (`TransportStop`: lat/lng, geofence
  radius, sequence, scheduled-arrival ETA), migration `20260628_0036`, `/transport/stops`
  CRUD and a stops page — replacing the legacy `TransportRoute.stops` JSON list.

## Roadmap (not yet built — intentionally out of scope of the foundation)

The full Smart Transport architecture (≈20 submodules) layers on top:

- **GPS tracking**: device → MQTT → transport service → Redis → WebSocket →
  dashboard/parent app (live position + ETA).
- **AI route optimizer**: nightly regeneration scored on fuel/distance/traffic/
  weather/road-closures (a TeducAI AI feature).
- **Boarding attendance**: QR / RFID / face recognition → attendance → parent
  notification; AI safety monitoring (missing student, wrong bus, never boarded).
- **Mobile apps**: parent (live track, ETA, report absence), student (today's
  bus/seat/ETA), driver (route, student list, attendance, incidents, fuel log).
- **Notification center**: push/SMS/email/WhatsApp fan-out for arrival/delay/
  boarding/route-change/emergency events.
- **Hostel integration**: weekend/holiday/airport/special trips.
- **Multi-school transport company**: one fleet serving many schools, each
  seeing only its own students.
- **Analytics**: occupancy, fuel/maintenance cost, route efficiency, driver
  performance, late arrivals, safety incidents, revenue/expense.
- **Microservice split**: keep Transport independently deployable, reusing
  platform identity/students/finance/attendance/timetable/notifications/AI.

When extending, keep the single-source-of-truth rule: read from core modules,
never duplicate, and keep every query tenant-scoped.

## Verification

- Backend: `python -m pytest backend/test_transport.py`
- Frontend: `npm run build` (cannot run in this sandbox — verify by inspection)

## i18n + TableFilter rollout

- All transport pages are now internationalised via the `transport` message namespace (FR/EN + ES/SW parity) — no hardcoded UI strings. Use `useTranslations("transport")` with dotted keys (`drivers.title`, `common.add`, etc.).
- Every list surface (drivers, vehicles, routes, stops, assignments, boarding, tracking positions, fleet-ops incidents) wires the shared `TableFilter`/`useTableFilter`. The dashboard is KPI cards (no collection) so it is i18n-only.
