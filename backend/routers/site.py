"""Public site CMS managed by the Super Admin.

`GET /site/content` is public (consumed by the marketing/landing pages).
`PUT /site/content` is restricted to the Super Admin and persists the editable
content as a single JSON document. Code-level defaults guarantee the public
site keeps rendering even before any content has been saved.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import audit, database, models, security

router = APIRouter(prefix="/site", tags=["Site CMS"])


DEFAULT_SITE_CONTENT: dict[str, Any] = {
    "hero": {
        "badge": "SaaS multi-établissements, sécurisé et international",
        "title": "TeducAI – La Plateforme Intelligente de Gestion des Établissements d’Enseignement et de Formation",
        "subtitle": "Automatisez la gestion administrative, académique et financière de votre établissement grâce à l’Intelligence Artificielle.",
        "primary_cta_label": "Essayer Gratuitement",
        "primary_cta_href": "/contact",
        "secondary_cta_label": "Demander une Démonstration",
        "secondary_cta_href": "/contact",
    },
    "partners": [
        "Écoles primaires",
        "Collèges et lycées",
        "Formation professionnelle",
        "Établissements techniques",
        "Universités et grandes écoles",
        "Instituts de recherche",
        "Formation continue",
        "Organismes de certification",
    ],
    "faq": [
        {
            "question": "TeducAI convient-il à tous les types d’établissements ?",
            "answer": "Oui. Primaire, secondaire, technique, professionnel, universitaire et formation continue sont pris en charge avec des modèles dédiés.",
        },
        {
            "question": "Les données de mon établissement sont-elles isolées ?",
            "answer": "Chaque établissement dispose d’une séparation stricte des données, par secteur, pays, devise et langue.",
        },
        {
            "question": "Puis-je payer en espèces ou en ligne ?",
            "answer": "TeducAI accepte les paiements en espèces validés par l’administration ainsi que Stripe, Djamo et CinetPay.",
        },
    ],
    "testimonials": [
        {
            "quote": "TeducAI a réduit notre charge administrative et fiabilisé nos encaissements.",
            "author": "Direction générale",
            "role": "Groupe scolaire",
        },
    ],
    "pricing": {
        "note": "Des offres adaptées aux établissements de toutes tailles. Contactez-nous pour une tarification personnalisée.",
    },
    "seo": {
        "meta_title": "TeducAI – Gestion intelligente des établissements d’enseignement",
        "meta_description": "Automatisez la gestion administrative, académique et financière de votre établissement grâce à l’Intelligence Artificielle.",
    },
    "footer": {
        "tagline": "La plateforme intelligente de gestion des établissements d’enseignement et de formation.",
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge stored content over defaults so partial saves keep working."""
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _get_or_create(db: Session) -> models.SiteContent:
    row = db.query(models.SiteContent).order_by(models.SiteContent.id).first()
    if not row:
        row = models.SiteContent(data={})
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/content")
def get_site_content(db: Session = Depends(database.get_db)) -> dict[str, Any]:
    """Public: merged site content (defaults overlaid with saved values)."""
    row = db.query(models.SiteContent).order_by(models.SiteContent.id).first()
    return _deep_merge(DEFAULT_SITE_CONTENT, row.data if row and isinstance(row.data, dict) else {})


@router.put("/content")
def update_site_content(
    payload: dict[str, Any],
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Super Admin: persist the editable public site content."""
    if current_user.role != models.UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super Administrateur uniquement.")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Contenu invalide.")

    row = _get_or_create(db)
    # Persist only the recognised top-level sections, merged over what exists.
    allowed = set(DEFAULT_SITE_CONTENT.keys())
    incoming = {key: value for key, value in payload.items() if key in allowed}
    row.data = _deep_merge(row.data if isinstance(row.data, dict) else {}, incoming)
    row.updated_by_id = current_user.id
    audit.record_audit(
        db,
        action="site_content.updated",
        current_user=current_user,
        entity_type="site_content",
        entity_id=row.id,
        details={"sections": list(incoming.keys())},
    )
    db.commit()
    db.refresh(row)
    return _deep_merge(DEFAULT_SITE_CONTENT, row.data if isinstance(row.data, dict) else {})
