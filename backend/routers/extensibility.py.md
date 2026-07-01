# extensibility.py
## Source File
- `backend/routers/extensibility.py`
## Purpose
- Platform Extensibility (`/extensibility`): outbound webhook endpoints (CRUD), delivery records with automatic-retry bookkeeping + manual retry, and tenant API keys (hashed; plaintext returned once). `emit_event(db, school_id, event_type, payload)` queues deliveries for subscribed endpoints — any module can publish events through it.
## Local Contracts
- Tenant-scoped; admin-gated. API keys store only sha256(key); never the plaintext. The actual HTTP sender/retry worker is a runtime component (NOT READY) — this owns the data model, subscription matching and exponential-backoff scheduling. GraphQL/plugin-marketplace/SDK remain roadmap.
## Verification
- `python -m pytest backend/test_extensibility.py`
- `GET /extensibility/deliveries` lists recent outbound deliveries (filter by status, newest first) so admins can monitor and use the retry endpoint.
