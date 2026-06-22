# ai_billing.py

## Source File

- `backend/routers/ai_billing.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.
- Exposes AI provider, targeted credit pack, manual cash/free validation, wallet limits, school-to-user allocation/revocation, platform payment, school payment, and AI usage APIs with Super Admin or tenant-scoped RBAC gates.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- School-payment creation and listing are isolated by the active school-model assignment.
- AI pack purchases accept cash, free, Stripe, Djamo, or CinetPay. Cash/free payments remain pending until Super Admin validation; configured online providers return a checkout URL and remain webhook-confirmed.
- School-targeted purchases require `ai_credits:create`; manual payment validation is Super Admin only and applies credits idempotently.
- Successful subscription webhooks activate the matching school subscription and update the school's current billing period.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
