# payment_gateway.py

## Source File

- `backend/services/payment_gateway.py`

## Purpose

- Creates external checkout sessions for Stripe, CinetPay Mobile Money, and a configurable Djamo payment endpoint.
- Returns an actionable pending-configuration state when provider credentials are absent instead of simulating payment success.

## Local Contracts

- Provider secrets are read from environment variables or supplied decrypted in memory by the caller.
- Provider responses must not be logged with secret request headers.
- Payment success remains webhook-driven; creating a checkout session never marks a payment successful.
- Stripe uses the provider's currency exponent rules: XOF/FCFA amounts are sent as zero-decimal units while ordinary two-decimal currencies use minor units.

## Verification

- `python -m py_compile backend\services\payment_gateway.py`
- CinetPay completion: channels configurable via CINETPAY_CHANNELS (default ALL = every method enabled on the merchant account: Orange/MTN/Moov/Wave/cards); checkout payload carries a generic customer block so card channels stay available. NEW `cinetpay_check_transaction(reference)` (server-side /v2/payment/check verification; ACCEPTED->successful, REFUSED/CANCELLED->failed, WAITING/PENDING->pending, unreachable->unknown = apply NOTHING) and `verify_cinetpay_token(x_token, form)` (HMAC-SHA256 over the CinetPay field order with CINETPAY_SECRET_KEY; passes when no secret is configured because the check API remains the authoritative gate).
