# test_payment_gateway.py

## Source File

- `backend/test_payment_gateway.py`

## Purpose

- Verifies that payment checkout creation reports missing Stripe configuration safely.
- Verifies that a successful Stripe provider response exposes the external reference and redirect URL.

## Verification

- `python -m pytest backend\test_payment_gateway.py`
