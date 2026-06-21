# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/checkout/page.tsx`

## Purpose

- Checkout page for items collected in the TeducAI cart.
- Lets users choose Stripe, Djamo, or CinetPay Mobile Money networks and creates backend checkout records.
- Redirects to the provider checkout URL when one is returned.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Keep platform and school payment wording clear.
- Keep payment providers aligned with `CheckoutRequest` backend schema.
- Preserve locale-aware navigation after successful checkout.
- Keep visible copy in the `checkout` and `app` translation namespaces.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/checkout/page.tsx"`
