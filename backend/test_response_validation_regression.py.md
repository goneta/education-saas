# test_response_validation_regression.py
## Purpose
- TestClient (full HTTP stack) regressions for the production 500s: /teachers and /auth/me tolerate a stored email strict EmailStr rejects (reserved domain); /account/cart tolerates a non-dict metadata_json. Goes through response_model serialization, which direct-call unit tests bypass.
## Verification
- `python -m pytest backend/test_response_validation_regression.py`
