# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/ai-credits/page.tsx`

## Purpose

- React/Next.js TypeScript component or page file. It participates in Next.js App Router routing.
- Provides the AI credits and separated payments dashboard: online purchases, Super Admin cash/free validation, user/school-targeted packs, school-to-user allocations and revocation, providers, wallets, usage, and transactions.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.
- Pack buttons open a localized payment dialog carrying pack, target wallet, amount, currency, and provider context.
- Cash/free purchases create pending manual-validation payments; Stripe, Djamo, and CinetPay follow returned checkout URLs. Super Admin can validate eligible pending payments from the platform-payment list.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
