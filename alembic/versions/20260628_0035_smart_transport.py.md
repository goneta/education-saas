# 20260628_0035_smart_transport.py

## Purpose

- Creates `transport_drivers` and `transport_vehicles` (Smart Transport master data) and adds nullable `driver_id`, `vehicle_id`, `capacity` columns to `transport_routes`.

## Local Contracts

- School-scoped tables. Route↔driver/vehicle links are column-only (FKs declared on the ORM model) because SQLite cannot `ALTER TABLE ADD CONSTRAINT`. Additive; legacy free-text driver/vehicle fields on `transport_routes` remain for back-compat.

## Verification

- `python -m alembic upgrade head`
- `python -m pytest backend/test_transport.py`
