# test_esignature.py — Tests for the in-house e-signature

## Coverage

- Sign + verify: parent signs a self-service document; `valid/authentic` true,
  code format XXXX-XXXX-XXXX; signatures surface in `/verify/{reference}` and
  `/mine`.
- Tamper evidence: mutating the document content AFTER signing flips
  `tampered=True` (authenticity still holds); forging the signature value
  flips `authentic=False`.
- Guards: double signature by the same signer → 409; student AND linked
  parent can each sign (2 rows); unlinked user → 403; unknown document → 404.

## Pattern

In-memory SQLite (StaticPool) + direct router/service calls, reusing the
self-documents generation flow to create the signed document.
