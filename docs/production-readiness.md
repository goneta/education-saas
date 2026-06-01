# Production readiness

## Implemented controls

- CI GitHub Actions: backend migrations/tests, frontend lint/build, critical Playwright E2E.
- Readiness and monitoring endpoints: `/ready`, `/health`, `/metrics`.
- Secure file storage API: authenticated upload/download/delete, MIME and extension validation, size limit, checksum, tenant scope, optional antivirus command.
- RBAC production permissions: files, audit, security, compliance, monitoring, approval and backup scopes.
- Compliance endpoints: school-scoped personal data export and user anonymization with audit log.
- Backup scripts: SQLite copy and PostgreSQL `pg_dump`/`pg_restore` wrappers with checksum metadata.
- Workflow locking: finalized approval-driven records cannot be directly mutated through generic enterprise CRUD.

## Production operator checklist

- Configure `SECRET_KEY` or `JWT_SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, provider secrets and `CORS_ALLOWED_ORIGINS`.
- Run `python -m alembic upgrade head` before each deployment.
- Configure `FILE_STORAGE_BACKEND`, storage path or bucket, `MAX_UPLOAD_BYTES`, allowed MIME types and `CLAMAV_SCAN_COMMAND`.
- Schedule `python -m backend.scripts.backup_database` and test restore with `ALLOW_RESTORE=true`.
- Scrape `/metrics` and alert on `/ready.ready=false`, DB errors, 5xx rate, failed notification spikes and high security event volume.
- Keep `storage/`, `backups/`, local DB files and Playwright artifacts out of Git.
- Review `/system/audit-logs`, `/system/security-events` and role permissions regularly.

## Remaining infrastructure tasks outside the application code

- Put Redis or a gateway-level limiter in front of all production API instances.
- Use private object storage with short-lived signed URLs for sensitive files when moving beyond local storage.
- Add WAF/CDN DDoS controls, centralized logs, uptime probes and encrypted off-site backups.
- Run dependency and secret scanning in the repository host.
