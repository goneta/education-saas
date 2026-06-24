# protected-route.tsx

## Source File

- `frontend/components/auth/protected-route.tsx`

## Purpose

- Guards authenticated dashboard routes and redirects users away from dashboards that do not match their account type.

## DOX Scope

- Nearest contract: `frontend/components/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Recruiter and external-student dashboard access is enforced here in addition to backend API checks.

## Verification

- cmd.exe /c "cd frontend&& npx eslint components/<path>"; npm run build for shared/layout changes
