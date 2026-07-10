# ai_billing.py

## Source File

- `backend/routers/ai_billing.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.
- Exposes AI provider, provider credit monitoring, targeted credit pack, manual cash/free validation, wallet limits, school-to-user allocation/revocation, platform payment, school payment, and AI usage APIs with Super Admin or tenant-scoped RBAC gates.

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
- Platform AI monitoring sums provider credits, sold/allocated platform credits, wallet balances, and stores the Super Admin low-credit threshold.
- `POST /platform/ai/sync-credits` and `POST /platform/ai/providers/{id}/sync-credits` (Super Admin only) fetch provider balances through `ai_credit_sync` where the provider API supports it (OpenRouter); unsupported providers keep their manual value and are reported as such. Each provider response carries `balance_api_supported`.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
- Platform webhook now delegates confirmation to payment_service.apply_platform_payment (shared with /payments/cinetpay/notify — zero duplication).
