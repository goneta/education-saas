# Purpose

Administrative workspace for student transfer decisions, duplicate-safe transactional imports, and strongly confirmed academic-year closure.

# Contracts

- Transfer actions call permission-protected backend workflows.
- Imports require preview before commit.
- Academic-year closure requires the exact confirmation text `CLOTURER`.
