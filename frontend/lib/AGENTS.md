# Purpose

- Own frontend utilities for config, formatting, localization, product copy, and shared helper functions.

# Ownership

- All files under `frontend/lib/`.

# Local Contracts

- Utilities must be framework-compatible with Next.js client/server boundaries.
- Config helpers must not expose secrets.
- Localization helpers must preserve French as default and support EN/ES/SW flows.
- Dashboard modules should call `requestConfirmation` for sensitive/destructive confirmation instead of browser-native prompts.

# Work Guidance

- Keep helpers pure where possible.
- Avoid module-level browser-only APIs unless the file is strictly client-side.

# Verification

- Targeted lint: `cmd.exe /c "cd frontend&& npx eslint lib/<path>.ts"`.

# Child DOX Index

- No child AGENTS.md files yet.
