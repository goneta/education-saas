# 20260628_0036_transport_stops.py

## Purpose

- Creates `transport_stops` (first-class bus stops: route_id, sequence, latitude/longitude, geofence radius, scheduled-arrival ETA, address), school-scoped and route-linked.

## Local Contracts

- FK to `transport_routes` and `schools`. Replaces the legacy `transport_routes.stops` JSON list (kept for back-compat). Additive.

## Verification

- `python -m alembic upgrade head`
- `python -m pytest backend/test_transport.py`
