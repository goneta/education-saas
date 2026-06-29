# test_hr.py
## Purpose
- Slice 5: leave self-create → approve lifecycle + notification; staff-sees-own vs admin-sees-all; non-admin cannot decide (403); end-before-start rejected (400). Uses the existing LeaveRequest model.
## Verification
- `python -m pytest backend/test_hr.py`
