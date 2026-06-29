# commerce.py

## Source File

- `backend/services/commerce.py`

## Purpose

- Implements cart item normalization and checkout conversion into platform payments or school payments.
- Keeps AI credit/subscription purchases separate from school fee, transport, canteen, registration, exam, and document-service payments.
- Creates provider checkout sessions and stores external references and redirect URLs on payment metadata.

## DOX Scope

- Nearest contract: `backend/services/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Platform item types must produce `PlatformPayment` records for Thunderfam/TeducAI revenue.
- School item types must produce `SchoolPayment` records for the connected school's payment accounts.
- Do not clear cart items until payment records have been created successfully.
- Mixed platform/school carts and mixed-currency carts must be checked out separately.
- Missing provider credentials must leave the cart intact and return an actionable configuration error.

## Verification

- `python -m py_compile backend\services\commerce.py`
- Add targeted checkout tests when changing payment behavior.
- `cart_item_response` normalizes a non-dict `metadata_json` to None (the JSON column can hold legacy non-dict values; the response contract is a dict). Fixes the `/account/cart` 500.
