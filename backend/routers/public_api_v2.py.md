# Public API v2 router

- Source: `backend/routers/public_api_v2.py`.
- Partner REST API under `/api/v2`, authenticated by `X-API-Key` and scoped to the API key's school.
- Write request models use namespaced `PublicV2*` schemas from `backend/schemas.py` so partner contract changes do not overwrite core registration and education schemas.
- Verification: `python -m pytest backend/test_public_v2_schema_isolation.py` and the full backend suite.
