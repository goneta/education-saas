# 20260622_0021_user_profile_photos.py

## Purpose

- Adds the persistent `users.profile_photo_url` reference used by student, teacher, staff, and account cards.

## Verification

- `python -m alembic upgrade head`
- `python -m pytest backend/test_system.py backend/test_students.py backend/test_teachers.py`
