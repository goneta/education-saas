# Purpose

- Own reusable backend service logic: AI, automation, notifications, file storage, credit accounting, provider integrations, and other cross-router business rules.

# Ownership

- All `backend/services/*.py` modules.

# Local Contracts

- Services that handle secrets must encrypt, mask, or avoid returning them.
- Services that mutate finance, AI credits, files, notifications, or tenant data must be deterministic and auditable through their callers.
- Provider integrations should tolerate missing credentials and report actionable failures.
- AI provider credit balances may only be auto-fetched where the provider API exposes them (e.g. OpenRouter); other providers keep a manually-entered value, and `ai_credit_sync` must report `unsupported`/`no_key`/`error` rather than raising or fabricating a balance.
- AI providers are auto-registered from `.env.production` keys by `ai_provider_bootstrap` (env-seeded rows tagged `account_label="env"`, refreshed on boot, never clobbering UI-created rows); `env_api_key_for` is the single source of truth for env key names and aliases used by the chat and sync paths.
- The TeducAI multi-agent roster lives in `ai_agents.py` (41 agents, source of truth for chat routing). Every agent prompt must embed the shared `SECURITY_PREAMBLE`; `select_agent` must stay permission-aware and side-effect free, and routing must never replace the per-request RBAC/tenant enforcement in the chat router.
- Checkout provider integrations must never mark payments successful before an authenticated provider webhook confirms the transaction.
- Payment adapters must normalize provider-specific currency rules, including zero-decimal XOF/FCFA amounts.

# Work Guidance

- Keep service APIs explicit and small; avoid hidden global state beyond configured environment settings.
- Add helper functions where shared calculations or validation rules would otherwise be duplicated across routers.
- School-to-user AI credit allocations must debit and credit paired wallets atomically, reject overdrafts, and refund only unconsumed credits on revocation.
- School document branding must be resolved through the shared school-document service rather than duplicated in individual PDF routes.
- School-model defaults must be seeded idempotently at assignment scope and active context must be validated through `school_context`.
- Student lifecycle mutations must use `student_lifecycle` helpers for global-profile reuse, enrollment resolution, schedule conflicts, academic-year editability, transfer access, and finance isolation.

# Verification

- Targeted syntax check: `python -m py_compile backend\\services\\<module>.py`.
- Backend service tests: `python -m pytest backend/test_<area>.py` when available.

# Child DOX Index

- No child AGENTS.md files yet.
