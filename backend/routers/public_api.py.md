# public_api.py

## Source File
- `backend/routers/public_api.py`

## Purpose
- Public partner REST API (`/api/v1`, OpenAPI-described): third-party, server-to-server access authenticated by a tenant API key sent as `X-API-Key` (hash lookup via `require_api_key`, updates `last_used_at`). Read-only, paginated (limit<=200) endpoints scoped to the key's school: /me, /students, /teachers, /classes, /subjects, /announcements (published only).

## Local Contracts
- 401 on missing/unknown/revoked keys. Minimal Public* DTOs (schemas.py) keep the surface deliberate. Keys are minted/revoked in /extensibility/api-keys.

## Verification
- `python -m pytest backend/test_public_api.py`
