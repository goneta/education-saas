# Purpose

- Own operational shell scripts used for production readiness, backup, restore, audit, smoke testing, and cron examples.

# Ownership

- `production/`: VPS/production helper scripts and cron examples.

# Local Contracts

- Scripts must be non-destructive by default and clearly communicate prerequisites, failures, and environment variables.
- Production scripts should work without Docker unless they explicitly document Docker requirements.
- Do not embed real secrets, passwords, or tokens in scripts.

# Work Guidance

- Prefer POSIX-compatible shell for VPS scripts unless a script documents a different runtime.
- Keep scripts idempotent where possible.

# Verification

- Shell syntax check when available: `bash -n scripts/production/<script>.sh`.
- Run smoke/audit scripts only when the target environment and variables are available.

# Child DOX Index

- No child AGENTS.md files yet. `production/` remains owned by this document.
