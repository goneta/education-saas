# Purpose

Centralizes the durable student lifecycle rules: global profiles, enrollment history, concurrent training, transfer access, academic-year locks, historical edit grants, and financial isolation.

# Contracts

- A legacy `StudentProfile` maps to exactly one `StudentGlobalProfile`.
- Every academic context is represented by a `StudentEnrollment`.
- Concurrent enrollments are limited to compatible technical, professional, vocational, modular, certification, evening, weekend, or internship contexts.
- Closed academic years are read-only unless the caller is Super Admin or has a valid audited grant.
- Financial data is visible only to the school owning the enrollment.
