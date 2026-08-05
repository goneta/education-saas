"""TTransportAI integration gateway — ARCHITECTURE PLACEHOLDER (no live calls).

The Smart Transport section is designed to become the entry point of the
external **TTransportAI** application. This module is the SINGLE seam where
that integration will plug in: the rest of TeducAI must talk to transport
features through it (never to TTransportAI directly) so the integration can
land later without any refactor.

Current state — deliberately NOT implemented (per product decision):
- No HTTP call is ever made from here yet.
- ``integration_status`` reports whether credentials are configured and always
  ``connected: False`` with an explicit message: nothing is faked.

When the TTransportAI API becomes available, implement inside this module:
    1. an authenticated HTTP client built from the env vars below;
    2. one function per capability (see ``CAPABILITIES``) mapping TeducAI
       entities (students, routes, stops, vehicles, drivers, escorts,
       subscriptions, live tracking, boarding, parent notifications,
       transport payments) to TTransportAI resources;
    3. verify-first webhooks for inbound events (same doctrine as CinetPay);
    4. transport payments MUST keep flowing through the existing centralized
       Payment Service (services/payment_service.py) — TTransportAI never
       becomes a second money path.

Environment variables (placeholders documented in .env.example):
    TTRANSPORTAI_API_URL   base URL of the TTransportAI API
    TTRANSPORTAI_API_KEY   tenant API key
"""

import os

# The functional domains the TTransportAI section will cover. Surfaced on the
# Transport hub so schools see the roadmap; each future client function should
# reference one of these keys.
CAPABILITIES = [
    {"key": "students", "label_fr": "Élèves transportés"},
    {"key": "routes", "label_fr": "Lignes et itinéraires"},
    {"key": "stops", "label_fr": "Arrêts"},
    {"key": "vehicles", "label_fr": "Véhicules"},
    {"key": "drivers", "label_fr": "Chauffeurs"},
    {"key": "escorts", "label_fr": "Accompagnateurs"},
    {"key": "subscriptions", "label_fr": "Abonnements de transport"},
    {"key": "live_tracking", "label_fr": "Suivi en temps réel des trajets"},
    {"key": "attendance", "label_fr": "Présences et absences à bord"},
    {"key": "parent_notifications", "label_fr": "Notifications aux parents"},
    {"key": "payments", "label_fr": "Paiements liés au transport"},
]


def is_configured() -> bool:
    return bool(os.getenv("TTRANSPORTAI_API_URL") and os.getenv("TTRANSPORTAI_API_KEY"))


def integration_status() -> dict:
    """Honest status for the Transport hub. ``connected`` stays False until a
    real client exists — configuration alone is not a connection."""
    configured = is_configured()
    return {
        "provider": "TTransportAI",
        "connected": False,  # no client implemented yet — never faked
        "configured": configured,
        "capabilities": CAPABILITIES,
        "message": (
            "Clés TTransportAI détectées — l'intégration API n'est pas encore développée."
            if configured
            else "Intégration TTransportAI à venir. La gestion locale du transport reste pleinement fonctionnelle."
        ),
    }
