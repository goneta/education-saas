# school_context.py

## Purpose

- Resolves and validates the active organization, school, school-model assignment, and academic year.
- Allows Super Admin access, organization-owner access, primary-school access, or active school membership.
- Rejects forged model or academic-year identifiers before business queries execute.

## Contract

- API clients may send `X-School-Model-Assignment-ID` and `X-Academic-Year-ID`.
- Missing headers fall back to persisted user preferences.
- Context resolution never trusts a frontend identifier without checking school access.
