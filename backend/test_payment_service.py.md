# test_payment_service.py

## Purpose

- Verifies the centralized Payment Service: webhook confirms a payment and updates the invoice; duplicate webhook is idempotent (invoice not double-credited); partial→full payment status transitions; bad webhook signature rejected (403); enabled-providers reflects active accounts; manual verify requires a manager role.

## Verification

- `python -m pytest backend/test_payment_service.py`
