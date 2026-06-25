# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/checkout/page.tsx`

## Purpose

- Checkout page for items collected in the TeducAI cart.
- Supports AI credit pack selection from active platform packs when opened with `purchase=ai-credits`, then adds the selected pack as a platform cart item before checkout.
- Lets users choose Stripe, Djamo, or CinetPay Mobile Money networks and creates backend checkout records.
- Redirects to the provider checkout URL when one is returned.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Keep platform and school payment wording clear.
- Keep payment providers aligned with `CheckoutRequest` backend schema.
- Preserve locale-aware navigation after successful checkout.
- The order summary must show item name, description, credits, unit price, subtotal, taxes, and total, updating immediately when the selected AI credit pack changes.
- Keep visible copy in the `checkout` and `app` translation namespaces.

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/checkout/page.tsx"`
