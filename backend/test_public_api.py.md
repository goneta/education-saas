# test_public_api.py

## Purpose
- Partner API: key auth (valid / missing / unknown / revoked -> 401), tenant scoping across two schools, announcement-publish queues a webhook delivery for subscribed endpoints only, catch-all (no event_types) endpoints receive everything, deliveries listing.

## Verification
- `python -m pytest backend/test_public_api.py`
