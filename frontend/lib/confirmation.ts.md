# confirmation.ts

## Purpose

- Exposes a promise-based request API for the shared TeducAI confirmation dialog.
- Allows dashboard modules to replace browser `confirm()` prompts without duplicating modal state.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint lib/confirmation.ts"`
