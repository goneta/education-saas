# test_ttransport_gateway.py
## Source File
- `backend/test_ttransport_gateway.py`
## Purpose
- The placeholder gateway is honest: unconfigured -> connected False +
  configured False + 11 capabilities + "à venir" message; configured (env keys
  set) -> configured True but STILL connected False (credentials alone are not
  a connection — no client exists yet).
## Verification
- `python -m pytest backend/test_ttransport_gateway.py` (2 green).
