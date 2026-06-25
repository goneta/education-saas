# 20260625_0028_employment_ats_expansion.py

## Purpose

- Extends TeducAI Emploi into an ATS-oriented data model with recruiter branding, subscriptions, AI credits, richer job offers, richer CV data, AI match scores, and employment notifications.

## Local Contracts

- Existing CVs, recruiters, offers, and applications remain valid because new structured fields are nullable or have safe defaults.
- Rich profile details use JSON columns for compatibility with internal and external students while avoiding disruptive table fan-out.

## Verification

- `python -m alembic heads`
- `python -m py_compile backend\models.py`
