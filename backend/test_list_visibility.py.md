# test_list_visibility.py

## Purpose
- Regression tests for the production "200 []" empty-lists bug: legacy students (profile but no StudentEnrollment) and legacy teachers (no TeacherAssignment, or assignment with NULL school_model_assignment_id) must appear in /students and /teachers; enrolled/assigned rows still appear; other-school rows stay hidden (tenant isolation).

## Verification
- `python -m pytest backend/test_list_visibility.py`
