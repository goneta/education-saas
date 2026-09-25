# Reference validation regression tests

- In-memory SQLite, disposed after each case; no developer data modified.
- Covers create/update collisions across global/local sources, inactive rows,
  legacy levels, unchanged codes, whitespace, rejected-update atomicity and
  malformed HTTP payloads. Separate schools can still reuse local codes.
- Run: `python -m pytest backend/test_reference_validation.py`.
