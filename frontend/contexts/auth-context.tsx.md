# auth-context.tsx

## Source File

- `frontend/contexts/auth-context.tsx`

## Purpose

- Owns authentication state, secure login/logout, idle timeout, user loading, and global API 401 session expiration handling.

## DOX Scope

- Nearest contract: `frontend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Invalid tokens are removed before the logout request to prevent recursive 401 handling, and locale-aware login redirection preserves a clear expiration message.
- Authenticated API requests automatically propagate cached school-model and academic-year IDs; the backend still validates both values.

## Verification

- cmd.exe /c "cd frontend&& npm run build" when relevant
