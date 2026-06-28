# Purpose

Administrative workspace for student transfer decisions, duplicate-safe transactional imports, and strongly confirmed academic-year closure.

# Contracts

- Transfer actions call permission-protected backend workflows.
- Imports require preview before commit.
- Academic-year closure requires the exact confirmation text `CLOTURER`.
- Record tables use the shared universal `TableFilter` / `useTableFilter` (column selector + debounced accent/case-insensitive search-as-you-type, persisted per `storageKey`); reuse it for any new collection rather than bespoke search inputs.
