# 20260629_0041_extensibility.py
## Purpose
- Creates `webhook_endpoints`, `webhook_deliveries` (retry bookkeeping), `api_keys` (hashed).
## Verification
- `python -m alembic upgrade head`; `python -m pytest backend/test_extensibility.py`
