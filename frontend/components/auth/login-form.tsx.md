# login-form.tsx

## Source File

- `frontend/components/auth/login-form.tsx`

## Purpose

- Renders the shared sign-in form and redirects successful logins to the correct role/account dashboard.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Redirect decisions use `frontend/lib/auth-routing.ts` and the authenticated `/auth/me` metadata.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
