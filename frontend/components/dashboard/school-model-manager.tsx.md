# school-model-manager.tsx

## Purpose

- Lets an authorized school administrator select multiple school models and idempotently initialize their reference data.
- Supports non-destructive activation and deactivation of existing model assignments.
- Lets an organization owner create an additional school with the selected models and defaults.

## Security

- Catalog and assignments are loaded from authenticated context APIs.
- Backend `settings:write` permission and school access checks remain authoritative.
