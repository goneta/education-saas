from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Any
from sqlalchemy.orm import Session
from backend import audit, database, models, rbac, security
from backend.services.ai_service import ai_service

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    type: str # 'chat' or 'content'
    message: str
    data: Optional[Any] = None

AI_REFUSAL = (
    "Je ne peux pas effectuer cette action, car votre rôle actuel ne dispose pas des autorisations nécessaires "
    "pour accéder à ces informations ou exécuter cette opération. Veuillez contacter votre administrateur si vous "
    "pensez qu’il s’agit d’une erreur."
)

SENSITIVE_PERMISSION_KEYWORDS = {
    "students:view": ["autre eleve", "autres eleves", "tous les eleves", "liste des eleves", "student list", "all students"],
    "teachers:view": ["enseignant", "professeur", "teacher", "formateur"],
    "parents:view": ["parent", "tuteur", "famille"],
    "payments:view": ["paiement", "solde", "impaye", "frais", "payment", "balance"],
    "finance_fees:view": ["finance", "recette", "caisse", "rapport financier", "fee report"],
    "grades:view": ["notes", "bulletin", "grade", "report card"],
    "audit:view": ["audit", "journal d'audit", "qui a fait", "logs"],
    "users:view": ["utilisateur", "compte utilisateur", "user account"],
    "settings:view": ["parametre", "configuration", "settings"],
    "roles:view": ["role", "permission", "droits"],
}

WRITE_KEYWORDS = ["cree", "creer", "modifier", "supprimer", "valider", "approuver", "rejeter", "create", "update", "delete", "approve"]


def _ai_scope_for_user(user: models.User, db: Session) -> dict:
    permissions = rbac.permission_snapshot(user, db)
    assigned_roles = permissions.get("roles", [user.role.value])
    if user.role in [models.UserRole.STUDENT, models.UserRole.PUPIL]:
        scope = "votre compte, vos notes, bulletins, devoirs, absences, emploi du temps et frais personnels"
    elif user.role == models.UserRole.PARENT:
        scope = "les dossiers scolaires, financiers et documents de vos enfants uniquement"
    elif user.role == models.UserRole.SUPER_ADMIN:
        scope = "toutes les donnees et tous les etablissements de la plateforme"
    elif user.role in [models.UserRole.SCHOOL_ADMIN, models.UserRole.ADMIN]:
        scope = "tous les modules de votre etablissement selon les permissions configurees"
    else:
        scope = "les donnees et modules autorises par vos permissions effectives"
    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
        "roles": assigned_roles,
        "school_id": user.school_id,
        "permissions": permissions.get("permissions", []),
        "scope_summary": scope,
        "refusal_sentence": AI_REFUSAL,
    }


def _required_permissions_for_message(message: str) -> list[str]:
    lower = message.lower()
    required = []
    for permission, keywords in SENSITIVE_PERMISSION_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            required.append(permission)
    if required and any(keyword in lower for keyword in WRITE_KEYWORDS):
        required = [permission.replace(":view", ":edit") for permission in required]
    return sorted(set(required))


def _is_cross_scope_request(message: str, user: models.User) -> bool:
    lower = message.lower()
    cross_scope_markers = ["autre eleve", "autres eleves", "autre famille", "tous les eleves", "toutes les familles", "all students", "other student"]
    if user.role in [models.UserRole.STUDENT, models.UserRole.PUPIL, models.UserRole.PARENT]:
        return any(marker in lower for marker in cross_scope_markers)
    return False


@router.post("/", response_model=ChatResponse)
async def chat_with_ai(
    request_body: ChatRequest,
    http_request: Request,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    try:
        context = _ai_scope_for_user(current_user, db)
        required_permissions = _required_permissions_for_message(request_body.message)
        denied_permissions = [permission for permission in required_permissions if not rbac.has_permission(current_user, permission, db)]
        if denied_permissions or _is_cross_scope_request(request_body.message, current_user):
            audit.record_audit(
                db,
                action="ai.request.denied",
                current_user=current_user,
                entity_type="ai_agent",
                entity_id=str(current_user.id),
                details={
                    "requested": request_body.message[:500],
                    "required_permissions": required_permissions,
                    "denied_permissions": denied_permissions,
                    "ip": http_request.client.host if http_request.client else None,
                    "result": "denied",
                },
            )
            db.commit()
            return {"type": "chat", "message": AI_REFUSAL, "data": None}

        audit.record_audit(
            db,
            action="ai.request.accepted",
            current_user=current_user,
            entity_type="ai_agent",
            entity_id=str(current_user.id),
            details={
                "requested": request_body.message[:500],
                "required_permissions": required_permissions,
                "ip": http_request.client.host if http_request.client else None,
                "result": "accepted",
            },
        )
        response = ai_service.generate_response(request_body.message, context)
        audit.record_audit(
            db,
            action="ai.response.generated",
            current_user=current_user,
            entity_type="ai_agent",
            entity_id=str(current_user.id),
            details={"response_type": response["type"], "result": "executed"},
        )
        db.commit()
        return response
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="AI service failed")
