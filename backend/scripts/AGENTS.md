# Purpose

- Own backend-specific operational scripts for database backup, restore, and backend maintenance.

# Ownership

- All files under `backend/scripts/`.

# Local Contracts

- Scripts must not embed real secrets.
- Backup and restore scripts must clearly report target database, output paths, and failures.

# Work Guidance

- Prefer environment-variable driven configuration.
- Keep scripts safe to inspect and predictable on a VPS.

# Verification

- Syntax check Python scripts with `python -m py_compile backend\\scripts\\<script>.py`.

# Child DOX Index

- No child AGENTS.md files yet.
