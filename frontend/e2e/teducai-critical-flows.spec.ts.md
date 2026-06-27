# teducai-critical-flows.spec.ts

## Source File

- `frontend/e2e/teducai-critical-flows.spec.ts`

## Purpose

- TypeScript source file for frontend configuration, helpers, or tests.

## DOX Scope

- Nearest contract: `frontend/e2e/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Generated E2E account emails use `example.com` so strict backend email validation accepts them.
- Teacher and parent phone fixtures use Cote d'Ivoire-compliant numbers (`+225` country code, 10 national digits) because a school's `country_code` defaults to `CI` unless set otherwise, and backend phone validation enforces the active country's prefix and digit length.

## Verification

- cmd.exe /c "cd frontend&& npx playwright test" when environment is available
