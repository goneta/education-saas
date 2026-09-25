# Public API v2 schema isolation regression

- Verifies that school registration retains country/localization fields and that core education contracts remain separate from partner API v2 request models.
- Run: `python -m pytest backend/test_public_v2_schema_isolation.py backend/test_admission_roster_visibility.py`.
