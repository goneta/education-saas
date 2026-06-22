# Purpose

Exposes the global student journey API: search, enrollment history, concurrent enrollment validation, transfers, academic-year closure, Super Admin edit grants, and permission-aware import/export.

# API contracts

- Financial history is emitted only for an enrollment owned by the caller's school.
- Transfer approval never grants financial visibility.
- Import is previewed and persisted as a batch before an explicit transactional commit.
- Exports support PDF, CSV, XLSX, Markdown, XML, and JSON and are audited.
