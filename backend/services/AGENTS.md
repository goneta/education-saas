# Purpose

- Own reusable backend service logic: AI, automation, notifications, file storage, credit accounting, provider integrations, and other cross-router business rules.

# Ownership

- All `backend/services/*.py` modules.

# Local Contracts

- Services that handle secrets must encrypt, mask, or avoid returning them.
- Services that mutate finance, AI credits, files, notifications, or tenant data must be deterministic and auditable through their callers.
- Provider integrations should tolerate missing credentials and report actionable failures.
- Checkout provider integrations must never mark payments successful before an authenticated provider webhook confirms the transaction.
- Payment adapters must normalize provider-specific currency rules, including zero-decimal XOF/FCFA amounts.

# Work Guidance

- Keep service APIs explicit and small; avoid hidden global state beyond configured environment settings.
- Add helper functions where shared calculations or validation rules would otherwise be duplicated across routers.
- School-to-user AI credit allocations must debit and credit paired wallets atomically, reject overdrafts, and refund only unconsumed credits on revocation.
- School document branding must be resolved through the shared school-document service rather than duplicated in individual PDF routes.
- School-model defaults must be seeded idempotently at assignment scope and active context must be validated through `school_context`.

# Verification

- Targeted syntax check: `python -m py_compile backend\\services\\<module>.py`.
- Backend service tests: `python -m pytest backend/test_<area>.py` when available.

# Child DOX Index

- No child AGENTS.md files yet.
