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
