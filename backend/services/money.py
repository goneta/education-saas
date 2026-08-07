"""Monetary arithmetic on FLOAT columns — residue-safe comparisons (MONEY-02).

Every amount is stored as `FLOAT` (`Fee.amount`, `StudentInvoice.amount_due`,
`Payment.amount`…). Converting the whole financial schema to `Numeric` is the
correct long-term fix, but it means migrating every money table and reviewing
every calculation — too much to do safely three weeks before the launch.

What is cheap and safe is to stop *comparing floats to zero*. The failure is
real and user-visible: `1.1 + 2.2` is `3.3000000000000003`, so an invoice paid
in full can keep a residual balance of 1e-16, stay `PARTIAL` forever and — via
`routers/students.py` — **block the pupil's certificate** even though the family
paid everything.

Two rules, applied everywhere money is compared:
- `normalize()` rounds a computed amount to the currency's precision before it
  is stored, so residue never accumulates in the database;
- `is_settled()` / `is_outstanding()` compare against `EPSILON` (half a cent)
  instead of against zero.

`EPSILON` is deliberately smaller than the smallest real-world amount (1 FCFA)
and larger than any plausible float residue.
"""

EPSILON = 0.005  # half a cent: below this, a balance is settled


def normalize(value: float | int | None) -> float:
    """Round a computed amount to the currency's precision before storing it."""
    return round(float(value or 0), 2)


def is_settled(balance: float | int | None) -> bool:
    """True when nothing meaningful is left to pay (never a strict `<= 0`)."""
    return float(balance or 0) <= EPSILON


def is_outstanding(balance: float | int | None) -> bool:
    """True when a real amount is still due — the blocking condition for
    certificates, transcripts and other finance-gated documents."""
    return not is_settled(balance)


def remaining(due: float | int | None, paid: float | int | None) -> float:
    """Remaining balance, normalized and clamped at zero (never negative)."""
    return max(normalize(normalize(due) - normalize(paid)), 0.0)
