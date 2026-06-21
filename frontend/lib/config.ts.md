# config.ts

## Source File

- `frontend/lib/config.ts`

## Purpose

- Exposes the public API base URL used by frontend requests.
- Removes trailing slashes from environment configuration to prevent accidental double-slash API paths.

## DOX Scope

- Nearest contract: `frontend/lib/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- cmd.exe /c "cd frontend&& npx eslint lib/<path>"
