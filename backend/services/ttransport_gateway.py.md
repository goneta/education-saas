# ttransport_gateway.py
## Source File
- `backend/services/ttransport_gateway.py`
## Purpose
- ARCHITECTURE PLACEHOLDER (deliberate, documented — no live HTTP call): the
  single seam where the future TTransportAI integration will plug in. All of
  TeducAI must reach transport features through this module so the integration
  lands later without refactor. `CAPABILITIES` lists the 11 functional domains
  (élèves transportés, lignes/itinéraires, arrêts, véhicules, chauffeurs,
  accompagnateurs, abonnements, suivi temps réel, présences à bord,
  notifications parents, paiements transport); `integration_status()` reports
  configuration (env TTRANSPORTAI_API_URL/API_KEY) honestly and ALWAYS
  `connected: False` until a real client ships — nothing faked.
## Local Contracts
- When implementing the real client: verify-first webhooks (same doctrine as
  CinetPay); transport payments KEEP flowing through the centralized Payment
  Service — TTransportAI must never become a second money path.
## Verification
- `python -m pytest backend/test_ttransport_gateway.py` (2 green).
