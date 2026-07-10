# 20260708_0053_document_registry.py
## Source File
- `alembic/versions/20260708_0053_document_registry.py`
## Purpose
- Creates `document_registry` (universal document authenticity records).
## Local Contracts
- New table only, inline FKs, idempotent. Unique(source_type, source_id) for
  idempotent registration. down_revision = 20260707_0052.
## Verification
- In-process `alembic upgrade head` on fresh SQLite creates the table.
