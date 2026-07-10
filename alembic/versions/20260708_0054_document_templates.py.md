# 20260708_0054_document_templates.py
## Source File
- `alembic/versions/20260708_0054_document_templates.py`
## Purpose
- Creates `document_templates` (per-school diploma/certificate templates).
## Local Contracts
- New table only, inline FKs, idempotent. down_revision = 20260708_0053.
## Verification
- In-process `alembic upgrade head` on fresh SQLite creates the table.
