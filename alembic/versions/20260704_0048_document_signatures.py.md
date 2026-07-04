# 20260704_0048_document_signatures.py

E-signature infrastructure: creates `document_signatures` (document FK, signer
FK, content_hash, HMAC signature, signed_at, unique (document, signer)).
Column-only FKs (SQLite-compatible).
