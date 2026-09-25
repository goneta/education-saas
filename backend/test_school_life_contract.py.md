# Shared school-life HTTP contract

- Twelve independent scenarios per module: Discipline, Exams, Activities,
  Health and Boarding. Each scenario has a fresh in-memory database.
- Exercises detail, search, pagination, update, deletion, tenant isolation for
  list/export/detail/update/delete, student write denial, required create fields
  and required-field preservation on PATCH.
- Run: `python -m pytest backend/test_school_life_contract.py`.
- This suite does not establish complete workflow, performance or browser coverage.
