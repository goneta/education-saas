# esignature.py — In-house e-signature infrastructure

## Purpose

Closes the last Phase-2 NOT-READY item with real cryptography, no external
signing provider:

- `content_hash` = SHA-256 of the document's canonical content (sorted-keys
  JSON) — freezes WHAT was signed.
- `signature` = HMAC-SHA256 keyed with a signing key derived from the
  platform `SECRET_KEY` (domain-separated `teducai-esignature::` prefix so
  JWT and signatures never share a raw key), over
  `document_id|reference|content_hash|signer_id|signed_at`.
- `verify_signature` recomputes BOTH: an HMAC mismatch = forged/corrupted
  signature (`authentic=False`); a content-hash mismatch = the document was
  modified after signing (`tampered=True`). `valid` requires both checks.
- `short_code` prints a human-friendly XXXX-XXXX-XXXX code on the document.

One signature per (document, signer) — `DocumentSignature` unique constraint;
`sign_document` raises 409 on a second attempt.

Honesty note: this is an integrity/authenticity signature bound to the
authenticated platform account (who/what/when + tamper evidence), not a
qualified electronic signature in the eIDAS sense.

## Verification

- `python -m pytest backend/test_esignature.py`
