# context.py

## Purpose

- Exposes the global school-model catalog, authorized context options, active-context persistence, model assignment, model deactivation, AI enablement, and assignment-level limits.

## Security

- Every context identifier is checked against Super Admin, organization ownership, primary school, or active membership access.
- Assignment mutations require `settings:write`.
- Context changes and assignment mutations are audited.

## Routes

- `GET /context/catalog`
- `GET /context/options`
- `GET /context/active`
- `PUT /context/active`
- `POST /context/organizations`
- `POST /context/schools`
- `POST /context/assignments`
- `PATCH /context/assignments/{assignment_id}`
