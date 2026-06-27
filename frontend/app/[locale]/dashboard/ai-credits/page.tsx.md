# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/ai-credits/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.
- Provides the AI credits and separated payments dashboard: online purchases, Super Admin cash/free validation, user/school-targeted packs, school-to-user allocations and revocation, providers, provider-level credit monitoring, low-credit threshold alerts, wallets, usage, and transactions.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Pack buttons open a localized payment dialog carrying pack, target wallet, amount, currency, and provider context.
- Cash/free purchases create pending manual-validation payments; Stripe, Djamo, and CinetPay follow returned checkout URLs. Super Admin can validate eligible pending payments from the platform-payment list.
- Credit allocation revocation uses the shared TeducAI confirmation dialog.
- Super Admin monitoring cards display configured provider credits, purchased/allocated credits, remaining platform credits, wallet balances, and a configurable low-credit threshold.
- Provider monitoring offers an API sync ("Synchroniser via API" globally, per-provider "Synchroniser (API)") for providers whose API exposes a balance (flagged by `balance_api_supported`), alongside the manual entry path for those that do not; the summary message reports how many were synced vs left on a manual value.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
