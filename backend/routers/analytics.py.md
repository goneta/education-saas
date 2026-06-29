# analytics.py
## Source File
- `backend/routers/analytics.py`
## Purpose
- Analytics & BI (`/analytics`): tenant-scoped CSV export (students/teachers/fees) and `/insights` AI narrative over headline KPIs (via ai_service, local fallback).
## Local Contracts
- Export/insights gated to admin/accountant roles; every query filtered by school_id. PDF/Excel and predictive analytics remain roadmap (CSV is the first export format).
## Verification
- `python -m pytest backend/test_analytics.py`
