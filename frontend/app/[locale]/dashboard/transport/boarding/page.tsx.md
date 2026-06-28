# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/transport/boarding/page.tsx`

## Purpose

- Boarding attendance: record a student boarding/alighting (manual/QR/RFID) via `/transport/boarding` and list events, with the shared universal `TableFilter`. Feeds the safety alerts and dashboard boardings KPI.

## Maintenance Notes

- Student option value is `student_profile.id`. The backend validates the student and route are in the tenant.
