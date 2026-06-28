from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Any
from sqlalchemy.orm import Session
from backend import audit, database, models, rbac, security
from backend.routers.ai_automation import maybe_run_chat_automation
from backend.services.ai_service import ai_service
from backend.services import ai_credits, ai_agents, school_context

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
    active_context = None
    try:
        active_context = school_context.resolve_context(db, user)
    except HTTPException:
        active_context = None
    assignment = db.query(models.SchoolModelAssignment).filter(
        models.SchoolModelAssignment.id == active_context.school_model_assignment_id
    ).first() if active_context else None
    if assignment and not assignment.ai_enabled:
        raise HTTPException(status_code=403, detail="L'IA est desactivee pour le modele scolaire actif.")
    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
        "roles": assigned_roles,
        "school_id": user.school_id,
        "organization_id": active_context.organization_id if active_context else None,
        "school_model_assignment_id": active_context.school_model_assignment_id if active_context else None,
        "school_model": assignment.school_model.code if assignment else None,
        "academic_year_id": active_context.academic_year_id if active_context else None,
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


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse, include_in_schema=False)
async def chat_with_ai(
    request_body: ChatRequest,
    http_request: Request,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    try:
        context = _ai_scope_for_user(current_user, db)
        # Multi-agent routing: pick the most qualified specialized agent and give
        # the model its domain persona (within the same RBAC context).
        routing = ai_agents.select_agent(request_body.message, current_user, db)
        agent = routing["agent"]
        context["active_agent"] = agent.name
        context["agent_domain"] = agent.domain
        context["agent_instructions"] = agent.system_prompt()
        if routing["handoff"]:
            context["handoff"] = routing["handoff"]
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
        ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(request_body.message))
        automation_result = maybe_run_chat_automation(request_body.message, db, current_user)
        if automation_result is not None:
            response_text = f"{automation_result.message}\n{automation_result.data}\n{automation_result.recommendations}"
            ai_credits.record_usage(db, current_user, request_body.message, response_text, "ai_agent_chat", automation_result.action)
            audit.record_audit(
                db,
                action="ai.automation.chat_executed" if automation_result.executed else "ai.automation.chat_pending_approval",
                current_user=current_user,
                entity_type="ai_agent",
                entity_id=str(current_user.id),
                details={
                    "agent": automation_result.agent_key,
                    "action": automation_result.action,
                    "requires_approval": automation_result.requires_approval,
                    "result": "executed" if automation_result.executed else "approval_required",
                },
            )
            db.commit()
            return {
                "type": "content",
                "message": automation_result.message,
                "data": {
                    "agent": automation_result.agent_key,
                    "action": automation_result.action,
                    "requires_approval": automation_result.requires_approval,
                    "data": automation_result.data,
                    "recommendations": automation_result.recommendations,
                },
            }
        response = ai_service.generate_response_from_config(request_body.message, context, db)
        provider = db.query(models.AIProvider).filter(models.AIProvider.id == response.get("provider_id")).first() if response.get("provider_id") else None
        ai_credits.record_usage(
            db,
            current_user,
            request_body.message,
            str(response.get("data") or response.get("message") or ""),
            "ai_agent_chat",
            "chat_response",
            provider=provider,
            model_name=response.get("model_name"),
            prompt_tokens=response.get("prompt_tokens"),
            completion_tokens=response.get("completion_tokens"),
        )
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
    except HTTPException as exc:
        if exc.status_code in {402, 429}:
            db.commit()
        else:
            db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="AI service failed")


@router.get("/agents")
def list_agents(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    """List the TeducAI multi-agent roster with, for each, whether the current
    user is authorized to use it (RBAC-aware)."""
    return {
        "count": len(ai_agents.AGENTS),
        "agents": [
            {
                "key": agent.key,
                "name": agent.name,
                "domain": agent.domain,
                "permission": agent.permission,
                "authorized": rbac.has_permission(current_user, agent.permission, db),
            }
            for agent in ai_agents.AGENTS
        ],
    }


@router.post("/route")
def route_request(
    request_body: ChatRequest,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    """Return which specialized agent would handle a message (orchestration
    transparency), whether the user is authorized, and candidate handoffs."""
    routing = ai_agents.select_agent(request_body.message, current_user, db)
    agent = routing["agent"]
    return {
        "agent": {"key": agent.key, "name": agent.name, "domain": agent.domain},
        "authorized": routing["authorized"],
        "candidates": routing["candidates"],
        "handoff": routing["handoff"],
        "refusal": routing["refusal"],
    }
