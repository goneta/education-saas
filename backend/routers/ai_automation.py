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
    {"key": "ai_coo", "name": "AI Chief Operating Officer", "permission": "ai_reports:view", "category": "Operations", "actions": ["daily_briefing", "operational_alerts", "cross_module_supervision"]},
    {"key": "workflow_automation", "name": "AI Workflow Automation Engine", "permission": "ai_automation:create", "category": "Automation", "actions": ["multi_step_workflows", "payment_to_receipt_flow", "notification_orchestration"]},
    {"key": "document_processing", "name": "AI Document Processing Center", "permission": "files:create", "category": "Documents", "actions": ["document_extraction", "field_validation", "record_creation_plan"]},
    {"key": "compliance_legal", "name": "AI Compliance & Legal Officer", "permission": "compliance:view", "category": "Compliance", "actions": ["gdpr_monitoring", "retention_checks", "missing_approvals"]},
    {"key": "curriculum_designer", "name": "AI Curriculum Designer", "permission": "subjects:create", "category": "Curriculum", "actions": ["program_structure", "course_modules", "learning_outcomes"]},
    {"key": "accreditation_assistant", "name": "AI Accreditation Assistant", "permission": "compliance:export", "category": "Accreditation", "actions": ["accreditation_report", "quality_review", "ministry_submission"]},
    {"key": "school_marketing", "name": "AI School Marketing Manager", "permission": "operations:view", "category": "Marketing", "actions": ["lead_followup", "campaign_plan", "recruitment_analytics"]},
    {"key": "transport_manager", "name": "AI Transport Manager", "permission": "transport:view", "category": "Transport", "actions": ["route_optimization", "driver_assignment", "parent_delay_alerts"]},
    {"key": "library_manager", "name": "AI Library Manager", "permission": "library:view", "category": "Library", "actions": ["book_recommendations", "late_returns", "inventory_audit"]},
    {"key": "discipline_behavior", "name": "AI Discipline & Behavior Manager", "permission": "students:view", "category": "Discipline", "actions": ["incident_patterns", "behavior_risk_score", "intervention_plan"]},
    {"key": "wellbeing_safeguarding", "name": "AI Wellbeing & Safeguarding Officer", "permission": "students:view", "category": "Safeguarding", "actions": ["wellbeing_signals", "safeguarding_alerts", "early_intervention"]},
    {"key": "substitute_teacher", "name": "AI Substitute Teacher Manager", "permission": "timetable:edit", "category": "Timetable", "actions": ["replacement_teacher", "classroom_assignment", "schedule_updates"]},
    {"key": "research_assistant", "name": "AI Research Assistant", "permission": "ai_assistant:view", "category": "University", "actions": ["paper_summary", "literature_review", "dataset_analysis"]},
    {"key": "alumni_management", "name": "AI Alumni Management System", "permission": "students:view", "category": "Alumni", "actions": ["alumni_tracking", "mentorship", "employment_outcomes"]},
    {"key": "career_prediction", "name": "AI Career Prediction Engine", "permission": "ai_predictive:view", "category": "Career", "actions": ["career_suggestions", "course_recommendations", "employer_matching"]},
    {"key": "procurement_manager", "name": "AI Procurement Manager", "permission": "inventory:view", "category": "Procurement", "actions": ["supplier_analysis", "purchase_requests", "inventory_forecasts"]},
    {"key": "meeting_assistant", "name": "AI Meeting Assistant", "permission": "operations:view", "category": "Meetings", "actions": ["agenda_generation", "minutes", "action_items"]},
    {"key": "voice_receptionist", "name": "AI Voice Receptionist", "permission": "ai_assistant:view", "category": "Reception", "actions": ["voice_answers", "parent_questions", "whatsapp_handoff"]},
    {"key": "multi_agent_collaboration", "name": "AI Multi-Agent Collaboration", "permission": "ai_reports:view", "category": "Orchestration", "actions": ["agent_team_plan", "cross_domain_findings", "coordinated_recommendations"]},
    {"key": "autonomous_school_management", "name": "AI Autonomous School Management", "permission": "ai_automation:create", "category": "Autonomous", "actions": ["detect_act_followup", "autonomous_reminders", "scheduled_operations"]},
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
    "ai_coo",
    "workflow_automation",
    "document_processing",
    "compliance_legal",
    "curriculum_designer",
    "accreditation_assistant",
    "school_marketing",
    "transport_manager",
    "library_manager",
    "discipline_behavior",
    "wellbeing_safeguarding",
    "substitute_teacher",
    "research_assistant",
    "alumni_management",
    "career_prediction",
    "procurement_manager",
    "meeting_assistant",
    "voice_receptionist",
    "multi_agent_collaboration",
    "autonomous_school_management",
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
        ("workflow_automation", ["workflow", "automate", "automatic", "automatiquement", "orchestrate"]),
        ("ai_coo", ["coo", "morning", "daily briefing", "today requires", "operations briefing"]),
        ("multi_agent_collaboration", ["multi-agent", "multi agent", "collaborate", "agents together"]),
        ("document_processing", ["passport", "birth certificate", "transcript", "medical certificate", "extract document", "ocr"]),
        ("autonomous_school_management", ["autonomous", "without human", "schedule follow-up", "auto reminder"]),
        ("compliance_legal", ["gdpr", "compliance", "legal", "retention", "consent", "safeguarding"]),
        ("curriculum_designer", ["curriculum", "program", "learning outcomes", "competency", "diploma in"]),
        ("accreditation_assistant", ["accreditation", "quality report", "program review"]),
        ("transport_manager", ["transport", "route", "pickup", "driver", "fuel"]),
        ("library_manager", ["library", "book", "borrowing", "late return"]),
        ("discipline_behavior", ["discipline", "behavior", "incident", "suspension", "detention"]),
        ("wellbeing_safeguarding", ["wellbeing", "safeguarding", "isolation", "decline"]),
        ("substitute_teacher", ["substitute", "replacement teacher", "teacher absent"]),
        ("procurement_manager", ["procurement", "supplier", "purchase order", "inventory forecast"]),
        ("meeting_assistant", ["meeting", "agenda", "minutes", "action items"]),
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
        "ai_coo": ["ai_reports:view", "payments:view", "students:view", "teachers:view", "internships:view"],
        "workflow_automation": ["ai_automation:create", "payments:create", "notifications:create", "files:create"],
        "document_processing": ["files:create", "students:create", "operations:create"],
        "compliance_legal": ["compliance:view", "audit:view", "settings:view"],
        "curriculum_designer": ["subjects:create", "programs:create", "ai_assistant:view"],
        "accreditation_assistant": ["compliance:export", "ai_reports:export", "enterprise:export"],
        "school_marketing": ["operations:view", "notifications:create", "admissions:view"],
        "transport_manager": ["transport:view", "enterprise:view", "notifications:create"],
        "library_manager": ["library:view", "library:edit"],
        "discipline_behavior": ["students:view", "attendance:view", "ai_predictive:view"],
        "wellbeing_safeguarding": ["students:view", "attendance:view", "ai_predictive:view"],
        "substitute_teacher": ["timetable:edit", "teachers:view", "notifications:create"],
        "research_assistant": ["ai_assistant:view", "documents:view"],
        "alumni_management": ["students:view", "operations:view"],
        "career_prediction": ["ai_predictive:view", "grades:view", "internships:view"],
        "procurement_manager": ["inventory:view", "accounting:view", "expenses:view"],
        "meeting_assistant": ["operations:view", "notifications:create"],
        "voice_receptionist": ["ai_assistant:view", "portal:view"],
        "multi_agent_collaboration": ["ai_reports:view", "ai_automation:create", "students:view", "payments:view"],
        "autonomous_school_management": ["ai_automation:create", "payments:create", "notifications:create", "audit:view"],
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


def _advanced_operations_snapshot(db: Session, user: models.User) -> Dict[str, Any]:
    finance = _finance_summary(db, user) if _has_any_permission(user, db, ["payments:view", "finance_fees:view", "finance:read"]) else {}
    attendance = _attendance_risk(db, user) if rbac.has_permission(user, "students:view", db) else {}
    timetable_conflicts = 0
    if hasattr(models, "TimetableConflict"):
        timetable_conflicts = _count(db, models.TimetableConflict, user)
    internships_overdue = 0
    if hasattr(models, "InternshipEvaluation"):
        internships_overdue = _count(db, models.InternshipEvaluation, user)
    return {
        "morning_briefing": [
            {"priority": "high", "label": "students_absence_risk", "count": len(attendance.get("at_risk", [])) if attendance else 0},
            {"priority": "high", "label": "unpaid_invoices_or_fees", "count": finance.get("overdue_count", 0) if finance else 0},
            {"priority": "medium", "label": "internship_evaluations_overdue", "count": internships_overdue},
            {"priority": "medium", "label": "classroom_conflicts", "count": timetable_conflicts},
            {"priority": "medium", "label": "revenue_gap", "value": finance.get("remaining", 0) if finance else 0},
        ],
        "actions_for_principal": [
            "Review absent or late students and assign follow-up owners.",
            "Ask finance to validate reminder campaigns for unpaid balances.",
            "Check internship evaluations and timetable conflicts before publication.",
        ],
        "source_modules": ["attendance", "finance", "internships", "timetable", "forecasting"],
    }


def _workflow_automation_plan(command: str) -> Dict[str, Any]:
    return {
        "workflow": "payment_to_accounting_receipt_notification_archive",
        "trigger": "validated_payment_or_financial_event",
        "steps": [
            {"order": 1, "action": "validate_payment", "status": "ready"},
            {"order": 2, "action": "generate_receipt", "status": "ready"},
            {"order": 3, "action": "update_student_account", "status": "ready"},
            {"order": 4, "action": "create_accounting_entry", "status": "ready"},
            {"order": 5, "action": "notify_parent", "status": "requires_notification_provider"},
            {"order": 6, "action": "notify_finance_office", "status": "requires_template"},
            {"order": 7, "action": "archive_receipt", "status": "ready"},
        ],
        "guardrails": ["RBAC check before execution", "tenant isolation", "audit every step", "approval required for destructive actions"],
        "source_command": command,
    }


def _document_processing_plan(command: str) -> Dict[str, Any]:
    return {
        "supported_uploads": ["passport", "birth_certificate", "transcript", "medical_certificate", "employment_contract", "student_record"],
        "pipeline": [
            "secure_upload",
            "antivirus_scan",
            "ocr_or_text_extraction",
            "field_detection",
            "data_validation",
            "record_creation_draft",
            "document_storage",
            "alerts_for_missing_or_expired_data",
        ],
        "extracted_fields_examples": {
            "passport": ["full_name", "date_of_birth", "document_number", "expiry_date", "nationality"],
            "birth_certificate": ["student_name", "parents", "birth_date", "birth_place"],
            "transcript": ["previous_school", "subjects", "grades", "academic_year"],
            "employment_contract": ["employee", "start_date", "salary", "contract_type", "expiry_date"],
        },
        "human_review": "Required before final record creation.",
        "source_command": command,
    }


def _multi_agent_plan(db: Session, user: models.User) -> Dict[str, Any]:
    finance = _finance_summary(db, user) if _has_any_permission(user, db, ["payments:view", "finance_fees:view", "finance:read"]) else {}
    attendance = _attendance_risk(db, user) if rbac.has_permission(user, "students:view", db) else {}
    academic = _academic_risk(db, user) if rbac.has_permission(user, "grades:view", db) else {}
    return {
        "collaboration_team": ["AI Finance Officer", "AI Attendance Manager", "AI Student Risk Detection", "AI Executive Command Center"],
        "combined_findings": {
            "finance": finance,
            "attendance": attendance,
            "academic": academic,
        },
        "coordinated_recommendations": [
            "Prioritize students with both unpaid balances and attendance decline.",
            "Route finance reminders through parent communication after safeguarding checks.",
            "Escalate high-risk students to direction with a single consolidated action plan.",
        ],
    }


def _autonomous_management_plan(command: str) -> Dict[str, Any]:
    return {
        "autonomous_loop": [
            "detect_event",
            "classify_risk",
            "choose_authorized_action",
            "execute_or_request_approval",
            "notify_stakeholders",
            "schedule_follow_up",
            "write_audit_trail",
        ],
        "example": {
            "event": "unpaid_invoice_detected",
            "actions": ["send_parent_reminder", "generate_finance_report", "notify_finance_office", "schedule_follow_up"],
            "approval_required": False,
        },
        "limits": ["destructive actions require approval", "tenant isolation always enforced", "provider availability required for real notifications"],
        "source_command": command,
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
    if key == "ai_coo":
        data = _advanced_operations_snapshot(db, user)
        return AIAutomationResponse(agent_key=key, action="daily_operations_briefing", executed=True, message="Briefing operationnel AI COO genere.", data=data, recommendations=data["actions_for_principal"])
    if key == "workflow_automation":
        data = _workflow_automation_plan(payload.command)
        return AIAutomationResponse(agent_key=key, action="workflow_automation_plan", executed=True, message="Workflow multi-etapes IA prepare.", data=data, recommendations=["Activer les connecteurs de notification avant execution automatique complete.", "Conserver le mode approval pour les actions sensibles."])
    if key == "document_processing":
        data = _document_processing_plan(payload.command)
        return AIAutomationResponse(agent_key=key, action="document_processing_pipeline", executed=True, message="Pipeline de traitement documentaire IA prepare.", data=data, recommendations=["Faire valider les champs extraits par la scolarite ou l'administration.", "Archiver le document source avec son audit de traitement."])
    if key == "multi_agent_collaboration":
        data = _multi_agent_plan(db, user)
        return AIAutomationResponse(agent_key=key, action="multi_agent_collaboration", executed=True, message="Collaboration multi-agents IA orchestree.", data=data, recommendations=data["coordinated_recommendations"])
    if key == "autonomous_school_management":
        data = _autonomous_management_plan(payload.command)
        return AIAutomationResponse(agent_key=key, action="autonomous_management_loop", executed=True, message="Boucle de gestion autonome IA preparee.", data=data, recommendations=["Commencer par les rappels et notifications non destructifs.", "Exiger validation humaine pour suppressions, changements contractuels et decisions disciplinaires."])
    if key == "registrar":
        data = _registrar_draft(payload.command)
        return AIAutomationResponse(agent_key=key, action="admission_draft", executed=True, message="Dossier d'admission analyse en mode brouillon securise.", data=data, recommendations=["Importer les documents scannes puis faire valider par la scolarite."])
    if key in {"teacher_assistant", "homework_creator", "document_generator", "help_center", "education_chat", "voice_assistant", "curriculum_designer", "research_assistant", "meeting_assistant", "voice_receptionist"}:
        data = _teaching_draft(payload.command, user)
        return AIAutomationResponse(agent_key=key, action="generated_content", executed=True, message="Contenu IA genere.", data=data, recommendations=["Relire et adapter le contenu avant publication."])
    if key in {"compliance_legal", "accreditation_assistant"}:
        data = {
            "checks": ["missing_consent", "expired_contracts", "data_retention", "approval_gaps", "quality_evidence"],
            "findings": _advanced_operations_snapshot(db, user),
            "report_sections": ["executive_summary", "evidence_register", "risk_register", "corrective_actions", "submission_readiness"],
        }
        return AIAutomationResponse(agent_key=key, action="compliance_accreditation_review", executed=True, message="Revue conformite/accreditation IA generee.", data=data, recommendations=["Verifier les preuves avant transmission officielle.", "Assigner un responsable aux actions correctives."])
    if key in {"transport_manager", "library_manager", "discipline_behavior", "wellbeing_safeguarding", "substitute_teacher", "school_marketing", "alumni_management", "career_prediction", "procurement_manager"}:
        data = {
            "capability": agent["actions"],
            "operational_model": "monitor_detect_recommend_execute_when_authorized",
            "required_data": ["records", "statuses", "responsible_users", "notification_templates", "approval_rules"],
            "next_actions": ["connect module data", "define thresholds", "enable notifications", "review first recommendations"],
        }
        return AIAutomationResponse(agent_key=key, action="advanced_agent_plan", executed=True, message=f"{agent['name']} a prepare son plan operationnel.", data=data, recommendations=["Configurer les donnees de reference du module.", "Demarrer en mode recommandation avant automatisation complete."])
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
