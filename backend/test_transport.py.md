# test_transport.py

## Purpose

- Session-level tests (in-memory SQLite) for the Smart Transport router: the driver→vehicle→route→assignment→dashboard happy path, cross-school student assignment rejection (404), non-manager write rejection (403), and tenant isolation on list endpoints.

## Verification

- `python -m pytest backend/test_transport.py`
