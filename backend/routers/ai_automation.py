from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import audit, database, models, rbac, security
from ..services import ai_credits
from ..services.ai_service import ai_service


router = APIRouter(prefix="/ai-automation", tags=["AI Automation"])

AI_REFUSAL = (
    "Je ne peux pas effectuer cette action, car votre rôle actuel ne dispose pas des autorisations nécessaires "
    "pour accéder à ces informations ou exécuter cette opération. Veuillez contacter votre administrateur si vous "
    "pensez qu'il s'agit d'une erreur."
)

DELETE_WORDS = ["delete", "supprimer", "effacer", "erase", "remove"]


class AIAutomationRequest(BaseModel):
    command: str = Field(min_length=2, max_length=4000)
    agent_key: Optional[str] = None
    dry_run: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AIAutomationResponse(BaseModel):
    agent_key: str
    action: str
    executed: bool
    requires_approval: bool = False
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


AI_AGENTS: List[Dict[str, Any]] = [
    {"key": "registrar", "name": "AI Registrar", "permission": "operations:view", "category": "Admissions", "actions": ["analyze_admission_file", "suggest_class", "detect_missing_documents", "generate_student_number"]},
    {"key": "finance_officer", "name": "AI Finance Officer", "permission": "finance:read", "category": "Finance", "actions": ["unpaid_fees", "forecast_income", "detect_duplicate_payments", "payment_reminders"]},
    {"key": "attendance_manager", "name": "AI Attendance Manager", "permission": "students:view", "category": "Attendance", "actions": ["attendance_risk", "absence_alerts", "lateness_alerts"]},
    {"key": "timetable_optimizer", "name": "AI Timetable Optimizer", "permission": "timetable:view", "category": "Timetable", "actions": ["conflict_summary", "optimization_advice"]},
    {"key": "examination_manager", "name": "AI Examination Manager", "permission": "exams:view", "category": "Exams", "actions": ["exam_schedule_plan", "invigilator_plan", "seating_plan_draft"]},
    {"key": "report_card_generator", "name": "AI Report Card Generator", "permission": "grades:view", "category": "Grades", "actions": ["report_card_summary", "ranking_summary", "comment_generation"]},
    {"key": "teacher_assistant", "name": "AI Teacher Assistant", "permission": "subjects:view", "category": "Teaching", "actions": ["lesson_plan", "activities", "homework"]},
    {"key": "homework_creator", "name": "AI Homework & Assessment Creator", "permission": "subjects:view", "category": "Teaching", "actions": ["quiz", "worksheet", "exam_draft"]},
    {"key": "risk_detection", "name": "AI Student Risk Detection", "permission": "ai_predictive:view", "category": "Predictive", "actions": ["academic_risk", "support_plan"]},
    {"key": "parent_relationship", "name": "AI Parent Relationship Officer", "permission": "portal:view", "category": "Parent", "actions": ["child_summary", "parent_explanation"]},
    {"key": "hr_manager", "name": "AI HR Manager", "permission": "teachers:view", "category": "HR", "actions": ["contract_draft", "leave_summary", "payroll_summary"]},
    {"key": "document_generator", "name": "AI Document Generator", "permission": "files:view", "category": "Documents", "actions": ["certificate_draft", "attestation_draft", "contract_draft"]},
    {"key": "school_inspector", "name": "AI School Inspector", "permission": "audit:view", "category": "Audit", "actions": ["missing_data_audit", "operational_findings"]},
    {"key": "ministry_reporting", "name": "AI Ministry Reporting Officer", "permission": "compliance:export", "category": "Compliance", "actions": ["ministry_summary", "statistics_export_plan"]},
    {"key": "education_chat", "name": "AI Education Chat Assistant", "permission": "ai_assistant:view", "category": "Chat", "actions": ["role_scoped_answer", "guided_action"]},
    {"key": "voice_assistant", "name": "AI Voice Assistant", "permission": "ai_assistant:view", "category": "Voice", "actions": ["voice_command_intent", "voice_guidance"]},
    {"key": "school_crm", "name": "AI School CRM", "permission": "operations:view", "category": "CRM", "actions": ["admission_pipeline", "lead_followup"]},
    {"key": "career_internship", "name": "AI Career & Internship Manager", "permission": "internships:view", "category": "Internships", "actions": ["match_students_companies", "employability_summary"]},
    {"key": "help_center", "name": "AI Knowledge Base & Help Center", "permission": "ai_assistant:view", "category": "Help", "actions": ["page_help", "field_help", "process_help"]},
    {"key": "executive_command", "name": "AI Executive Command Center", "permission": "ai_reports:view", "category": "Executive", "actions": ["executive_summary", "critical_issues", "predictions"]},
]

CHAT_AUTOMATION_AGENT_KEYS = {
    "registrar",
    "finance_officer",
    "attendance_manager",
    "timetable_optimizer",
    "examination_manager",
    "report_card_generator",
    "teacher_assistant",
    "homework_creator",
    "risk_detection",
    "parent_relationship",
    "hr_manager",
    "document_generator",
    "school_inspector",
    "ministry_reporting",
    "school_crm",
    "career_internship",
    "help_center",
    "executive_command",
}


def _school_id(user: models.User) -> Optional[int]:
    return user.school_id


def _agent(agent_key: Optional[str], command: str) -> Dict[str, Any]:
    if agent_key:
        found = next((agent for agent in AI_AGENTS if agent["key"] == agent_key), None)
        if found:
            return found
    lower = command.lower()
    keyword_map = [
        ("finance_officer", ["fee", "fees", "invoice", "payment", "cash", "finance", "impaye", "paiement", "facture"]),
        ("attendance_manager", ["attendance", "absence", "late", "retard", "absent"]),
        ("timetable_optimizer", ["timetable", "emploi du temps", "schedule"]),
        ("report_card_generator", ["report card", "bulletin", "grades", "notes", "ranking"]),
        ("registrar", ["admission", "registration", "register", "inscription", "student id"]),
        ("career_internship", ["internship", "stage", "career", "employability"]),
        ("school_inspector", ["audit", "missing", "inspection", "incomplete"]),
        ("executive_command", ["executive", "summary", "dashboard", "statistics", "today"]),
        ("teacher_assistant", ["lesson", "cours", "plan", "exercise", "homework"]),
        ("document_generator", ["certificate", "attestation", "document", "diploma", "contract"]),
    ]
    for key, keywords in keyword_map:
        if any(word in lower for word in keywords):
            return next(agent for agent in AI_AGENTS if agent["key"] == key)
    return next(agent for agent in AI_AGENTS if agent["key"] == "education_chat")


def infer_agent_key(command: str) -> str:
    return _agent(None, command)["key"]


def _check_permission(user: models.User, db: Session, permission: str) -> None:
    if not rbac.has_permission(user, permission, db):
        raise HTTPException(status_code=403, detail=AI_REFUSAL)


def _has_any_permission(user: models.User, db: Session, permissions: List[str]) -> bool:
    return any(rbac.has_permission(user, permission, db) for permission in permissions)


def _agent_permissions(agent: Dict[str, Any]) -> List[str]:
    base = [agent["permission"]]
    fallback_permissions = {
        "finance_officer": ["payments:view", "invoices:view", "finance_fees:view", "accounting:view"],
        "teacher_assistant": ["ai_assistant:view", "subjects:view", "classes:view"],
        "homework_creator": ["ai_assistant:view", "subjects:view", "grades:create"],
        "document_generator": ["files:view", "report_cards:print", "receipts:print"],
        "school_inspector": ["audit:view", "monitoring:view", "settings:view"],
        "ministry_reporting": ["compliance:export", "ai_reports:export", "enterprise:export"],
        "executive_command": ["ai_reports:view", "payments:view", "students:view"],
    }
    return sorted(set(base + fallback_permissions.get(agent["key"], [])))


def _check_agent_permission(user: models.User, db: Session, agent: Dict[str, Any]) -> None:
    if not _has_any_permission(user, db, _agent_permissions(agent)):
        raise HTTPException(status_code=403, detail=AI_REFUSAL)


def _count(db: Session, model, user: models.User) -> int:
    query = db.query(func.count(model.id))
    if hasattr(model, "school_id") and user.school_id:
        query = query.filter(model.school_id == user.school_id)
    return int(query.scalar() or 0)


def _finance_summary(db: Session, user: models.User) -> Dict[str, Any]:
    query = db.query(models.Fee)
    if user.school_id:
        query = query.filter(models.Fee.school_id == user.school_id)
    fees = query.all()
    total_expected = sum(fee.amount for fee in fees)
    total_paid = sum(fee.total_paid for fee in fees)
    overdue = [fee for fee in fees if fee.status == models.FeeStatus.OVERDUE or fee.remaining_balance > 0]
    duplicate_payments = []
    payment_rows = db.query(models.Payment).join(models.Fee)
    if user.school_id:
        payment_rows = payment_rows.filter(models.Fee.school_id == user.school_id)
    grouped: Dict[str, int] = {}
    for payment in payment_rows.all():
        key = f"{payment.fee_id}:{payment.amount}:{payment.payment_date.date() if payment.payment_date else ''}"
        grouped[key] = grouped.get(key, 0) + 1
    duplicate_payments = [key for key, count in grouped.items() if count > 1]
    return {
        "expected": total_expected,
        "paid": total_paid,
        "remaining": max(total_expected - total_paid, 0),
        "overdue_count": len(overdue),
        "overdue_students": [
            {
                "fee_id": fee.id,
                "student_id": fee.student_id,
                "student": fee.student.user.full_name if fee.student and fee.student.user else None,
                "title": fee.title,
                "remaining": fee.remaining_balance,
            }
            for fee in overdue[:50]
        ],
        "duplicate_payment_signatures": duplicate_payments[:20],
    }


def _attendance_risk(db: Session, user: models.User) -> Dict[str, Any]:
    since = datetime.utcnow() - timedelta(days=30)
    query = db.query(models.Attendance).join(models.StudentProfile)
    if user.school_id:
        query = query.join(models.User, models.StudentProfile.user_id == models.User.id).filter(models.User.school_id == user.school_id)
    rows = query.filter(models.Attendance.date >= since).all()
    by_student: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        bucket = by_student.setdefault(row.student_id, {"student_id": row.student_id, "absent": 0, "late": 0, "total": 0, "name": row.student.user.full_name if row.student and row.student.user else None})
        bucket["total"] += 1
        if row.status == models.AttendanceStatus.ABSENT:
            bucket["absent"] += 1
        if row.status == models.AttendanceStatus.LATE:
            bucket["late"] += 1
    risks = []
    for item in by_student.values():
        score = item["absent"] * 2 + item["late"]
        if score >= 3:
            item["risk_level"] = "high" if score >= 6 else "medium"
            risks.append(item)
    return {"period_days": 30, "at_risk": sorted(risks, key=lambda row: (row["absent"], row["late"]), reverse=True)[:50]}


def _academic_risk(db: Session, user: models.User) -> Dict[str, Any]:
    query = db.query(models.StudentProfile)
    if user.school_id:
        query = query.join(models.User).filter(models.User.school_id == user.school_id)
    result = []
    for student in query.all():
        grades = [grade.score for grade in student.grades]
        average = sum(grades) / len(grades) if grades else None
        absences = db.query(func.count(models.Attendance.id)).filter(
            models.Attendance.student_id == student.id,
            models.Attendance.status == models.AttendanceStatus.ABSENT,
        ).scalar() or 0
        risk = "low"
        if average is None or average < 8 or absences >= 6:
            risk = "high"
        elif average < 10 or absences >= 3:
            risk = "medium"
        if risk != "low":
            result.append({
                "student_id": student.id,
                "student": student.user.full_name if student.user else None,
                "average": average,
                "absences": int(absences),
                "risk": risk,
                "recommendation": "Planifier un suivi pedagogique et informer le parent/tuteur.",
            })
    return {"students_at_risk": result[:50]}


def _executive_summary(db: Session, user: models.User) -> Dict[str, Any]:
    finance = _finance_summary(db, user) if _has_any_permission(user, db, ["payments:view", "finance_fees:view", "finance:read"]) else {}
    attendance = _attendance_risk(db, user) if rbac.has_permission(user, "students:view", db) else {}
    return {
        "academics": {
            "students": _count(db, models.StudentProfile, user),
            "teachers": _count(db, models.User, user),
            "classes": _count(db, models.Class, user),
            "timetables": _count(db, models.Timetable, user),
        },
        "finance": finance,
        "operations": {
            "internships": _count(db, models.Internship, user),
            "partner_companies": _count(db, models.PartnerCompany, user),
            "admissions": _count(db, models.AdmissionApplication, user),
        },
        "attendance": attendance,
        "ai_insights": [
            "Verifier les frais impayes et les eleves avec absences repetees.",
            "Controler les emplois du temps en brouillon avant publication.",
            "Prioriser les dossiers d'admission incomplets et les stages sans evaluation finale.",
        ],
    }


def _registrar_draft(command: str) -> Dict[str, Any]:
    now = datetime.utcnow()
    return {
        "document_extraction": {
            "supported_documents": ["birth_certificate", "national_id", "passport", "previous_school_report"],
            "ocr_status": "ready_for_uploaded_files",
            "confidence": "requires_human_review",
        },
        "generated_identifiers": {
            "admission_number": f"ADM-{now:%Y%m%d%H%M%S}",
            "student_number": f"STD-{now:%Y%m%d%H%M%S}",
        },
        "suggested_class": "A confirmer selon age, ancien niveau et bulletin precedent.",
        "missing_documents_checklist": ["Extrait de naissance", "Piece d'identite parent/tuteur", "Bulletin precedent"],
        "next_step": "Verifier les champs extraits puis valider la creation du profil eleve.",
        "source_command": command,
    }


def _teaching_draft(command: str, user: models.User) -> Dict[str, Any]:
    response = ai_service.generate_response(command, {
        "role": user.role.value,
        "scope_summary": "generation pedagogique autorisee selon le role connecte",
    })
    return {"draft": response.get("data") or response.get("message"), "response_type": response.get("type")}


def _execute(agent: Dict[str, Any], payload: AIAutomationRequest, db: Session, user: models.User) -> AIAutomationResponse:
    lower = payload.command.lower()
    if any(word in lower for word in DELETE_WORDS):
        return AIAutomationResponse(
            agent_key=agent["key"],
            action="approval_required",
            executed=False,
            requires_approval=True,
            message="Action destructive detectee. L'IA a prepare une demande de validation administrateur au lieu de supprimer directement.",
            data={"requested_command": payload.command, "approval_workflow": "admin_validation_required"},
            recommendations=["Faire valider la demande par un administrateur autorise avant execution."],
        )

    key = agent["key"]
    if key == "finance_officer":
        data = _finance_summary(db, user)
        return AIAutomationResponse(agent_key=key, action="finance_summary", executed=True, message="Synthese financiere IA generee.", data=data, recommendations=["Envoyer des rappels aux familles en retard.", "Verifier les signatures de paiements dupliques."])
    if key == "attendance_manager":
        data = _attendance_risk(db, user)
        return AIAutomationResponse(agent_key=key, action="attendance_risk", executed=True, message="Analyse des absences et retards generee.", data=data, recommendations=["Notifier les parents des eleves a risque.", "Creer un cas de suivi pour les absences repetees."])
    if key in {"risk_detection", "report_card_generator"}:
        data = _academic_risk(db, user)
        return AIAutomationResponse(agent_key=key, action="academic_risk", executed=True, message="Detection du risque academique generee.", data=data, recommendations=["Planifier du soutien cible.", "Verifier les notes manquantes avant publication des bulletins."])
    if key == "executive_command":
        data = _executive_summary(db, user)
        return AIAutomationResponse(agent_key=key, action="executive_summary", executed=True, message="Executive summary IA genere.", data=data, recommendations=data["ai_insights"])
    if key == "registrar":
        data = _registrar_draft(payload.command)
        return AIAutomationResponse(agent_key=key, action="admission_draft", executed=True, message="Dossier d'admission analyse en mode brouillon securise.", data=data, recommendations=["Importer les documents scannes puis faire valider par la scolarite."])
    if key in {"teacher_assistant", "homework_creator", "document_generator", "help_center", "education_chat", "voice_assistant"}:
        data = _teaching_draft(payload.command, user)
        return AIAutomationResponse(agent_key=key, action="generated_content", executed=True, message="Contenu IA genere.", data=data, recommendations=["Relire et adapter le contenu avant publication."])
    if key == "career_internship":
        data = {
            "internships": _count(db, models.Internship, user),
            "partner_companies": _count(db, models.PartnerCompany, user),
            "matching_rules": ["filiere/programme", "competences", "ville/pays", "capacite entreprise", "historique evaluation"],
        }
        return AIAutomationResponse(agent_key=key, action="internship_matching_plan", executed=True, message="Plan de matching stages/carrieres genere.", data=data, recommendations=["Completer les competences et objectifs des profils et entreprises."])
    if key == "school_inspector":
        data = {
            "missing_grades_hint": "Comparer assessments et grades par classe.",
            "missing_invoices": _finance_summary(db, user).get("overdue_count", 0) if _has_any_permission(user, db, ["payments:view", "finance_fees:view", "finance:read"]) else None,
            "draft_timetables": db.query(func.count(models.Timetable.id)).filter(models.Timetable.status != "published").scalar() or 0,
        }
        return AIAutomationResponse(agent_key=key, action="school_audit", executed=True, message="Inspection IA realisee.", data=data, recommendations=["Traiter les donnees manquantes avant rapports officiels."])
    data = {"planned_capability": agent["actions"], "status": "workflow_ready", "command": payload.command}
    return AIAutomationResponse(agent_key=key, action="workflow_plan", executed=True, message=f"{agent['name']} est pret a assister ce workflow.", data=data, recommendations=["Configurer les connecteurs et templates propres a l'etablissement pour automatiser davantage."])


def run_agent_command(
    command: str,
    db: Session,
    user: models.User,
    agent_key: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    dry_run: bool = True,
) -> AIAutomationResponse:
    payload = AIAutomationRequest(command=command, agent_key=agent_key, dry_run=dry_run, parameters=parameters or {})
    agent = _agent(payload.agent_key, payload.command)
    _check_agent_permission(user, db, agent)
    return _execute(agent, payload, db, user)


def maybe_run_chat_automation(command: str, db: Session, user: models.User) -> Optional[AIAutomationResponse]:
    agent = _agent(None, command)
    if agent["key"] not in CHAT_AUTOMATION_AGENT_KEYS:
        return None
    lower = command.lower()
    command_markers = [
        "show", "list", "generate", "create", "analyze", "audit", "predict", "forecast",
        "montre", "liste", "genere", "crée", "cree", "analyse", "prédis", "prevois",
        "summary", "statistiques", "rapport", "impaye", "absence", "stage", "timetable",
    ]
    if not any(marker in lower for marker in command_markers):
        return None
    return run_agent_command(command=command, db=db, user=user, agent_key=agent["key"], dry_run=True)


@router.get("/agents")
def list_agents(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    visible = []
    for agent in AI_AGENTS:
        item = dict(agent)
        item["enabled"] = _has_any_permission(current_user, db, _agent_permissions(agent))
        visible.append(item)
    return visible


@router.get("/executive-summary")
def executive_summary(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db)):
    if not _has_any_permission(current_user, db, ["ai_reports:view", "students:view", "payments:view"]):
        raise HTTPException(status_code=403, detail=AI_REFUSAL)
    return _executive_summary(db, current_user)


@router.post("/run", response_model=AIAutomationResponse)
def run_automation(
    payload: AIAutomationRequest,
    request: Request,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    agent = _agent(payload.agent_key, payload.command)
    _check_agent_permission(current_user, db, agent)
    try:
        ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(payload.command))
        result = _execute(agent, payload, db, current_user)
        ai_credits.record_usage(
            db,
            current_user,
            payload.command,
            f"{result.message}\n{result.data}\n{result.recommendations}",
            "ai_command_center",
            result.action,
        )
        audit.record_audit(
            db,
            action="ai_automation.executed" if result.executed else "ai_automation.approval_required",
            current_user=current_user,
            entity_type="ai_automation",
            entity_id=agent["key"],
            details={
                "command": payload.command[:500],
                "agent": agent["key"],
                "action": result.action,
                "requires_approval": result.requires_approval,
                "ip": request.client.host if request.client else None,
            },
        )
        db.commit()
        return result
    except HTTPException:
        db.commit()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI automation failed: {exc}") from exc
