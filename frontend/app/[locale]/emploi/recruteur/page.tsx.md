# page.tsx

## Source File

- `frontend/app/[locale]/emploi/recruteur/page.tsx`

## Purpose

- Public recruiter registration page for TeducAI Emploi accounts and recruiter subscription selection.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Recruiter accounts must remain scoped to TeducAI Emploi and must not imply school data access.
- Payment provider/status is handled by the backend.
- Newly created recruiter users must be sent to login so `/auth/me` can route them into the recruiter dashboard after authentication.
- Backend validation errors should be mapped to field-level messages, especially duplicate email and phone/password validation, without rendering raw JSON.
- Server failures should show a service-unavailable registration message, while 400/422/409 responses remain field-aware validation errors.
- The form pre-validates the backend password policy before sending the request.
- Successful registration redirects to login instead of leaving the registration form visible.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/emploi/recruteur/page.tsx"`
