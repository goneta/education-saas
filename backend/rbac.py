from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models


STANDARD_ACTIONS = [
    "view",
    "create",
    "edit",
    "delete",
    "approve",
    "reject",
    "export",
    "import",
    "print",
    "download",
    "share",
    "archive",
    "restore",
    "manage_settings",
    "full_access",
]

PERMISSION_MODULES = [
    ("students", "Gestion des etudiants", "Academique"),
    ("parents", "Gestion des parents", "Utilisateurs"),
    ("teachers", "Gestion des enseignants", "Ressources Humaines"),
    ("classes", "Classes", "Academique"),
    ("programs", "Filieres", "Academique"),
    ("levels", "Niveaux", "Academique"),
    ("subjects", "Matieres", "Academique"),
    ("timetable", "Emplois du temps", "Academique"),
    ("exams", "Examens", "Academique"),
    ("grades", "Notes", "Academique"),
    ("report_cards", "Bulletins", "Documents"),
    ("finance_fees", "Frais scolaires", "Finance"),
    ("invoices", "Factures", "Finance"),
    ("payments", "Paiements", "Finance"),
    ("receipts", "Recus", "Finance"),
    ("expenses", "Depenses", "Depenses"),
    ("accounting", "Comptabilite", "Comptabilite"),
    ("messages", "Messages", "Communication"),
    ("notifications", "Notifications", "Notifications"),
    ("emails", "Emails", "Email"),
    ("sms", "SMS", "Communication"),
    ("ai_assistant", "Assistant IA", "Intelligence Artificielle"),
    ("ai_reports", "Rapports IA", "Intelligence Artificielle"),
    ("ai_predictive", "Analyse predictive", "Intelligence Artificielle"),
    ("ai_automation", "Automatisation IA", "Intelligence Artificielle"),
    ("settings", "Parametres generaux", "Parametres"),
    ("roles", "Gestion des roles", "Securite"),
    ("users", "Gestion des utilisateurs", "Utilisateurs"),
    ("audit", "Journaux d'activite", "Audit"),
    ("backups", "Sauvegardes", "Securite"),
    ("security", "Securite", "Securite"),
    ("files", "Documents", "Documents"),
    ("portal", "Portails", "Utilisateurs"),
    ("operations", "Admissions et operations", "Admissions"),
    ("enterprise", "Modules enterprise", "Rapports"),
    ("compliance", "Conformite", "Securite"),
    ("monitoring", "Monitoring", "Audit"),
    ("library", "Bibliotheque", "Bibliotheque"),
    ("transport", "Transport", "Transport"),
    ("canteen", "Cantine", "Transport"),
    ("inventory", "Inventaire", "Inventaire"),
]

ACTION_ALIASES = {
    "read": "view",
    "write": "edit",
    "issue": "create",
    "receipt": "print",
    "run": "create",
    "erase": "delete",
}

LEGACY_ALIASES = {
    "students": ["students"],
    "teachers": ["teachers"],
    "finance": ["finance_fees", "invoices", "payments", "receipts", "expenses", "accounting"],
    "pedagogy": ["classes", "programs", "levels", "subjects", "timetable", "exams", "grades", "report_cards"],
    "grades": ["grades", "report_cards"],
    "attendance": ["students", "classes"],
    "operations": ["operations"],
    "enterprise": ["enterprise"],
    "files": ["files"],
    "reports": ["report_cards", "accounting", "ai_reports"],
    "documents": ["receipts", "report_cards", "files"],
    "settings": ["settings"],
    "audit": ["audit"],
    "security": ["security"],
    "compliance": ["compliance"],
    "monitoring": ["monitoring"],
    "backup": ["backups"],
    "portal": ["portal"],
}

DEFAULT_ROLE_DEFINITIONS = [
    ("super_admin", "Super Administrateur", "Administration", "Proprietaire de la plateforme SaaS.", "#7C3AED", True),
    ("school_admin", "Administrateur", "Administration", "Administre l'etablissement et ses donnees.", "#0F766E", True),
    ("admin", "Administrateur", "Administration", "Role administratif configurable.", "#0F766E", True),
    ("direction", "Direction", "Direction", "Supervise la gestion globale de l'etablissement.", "#1D4ED8", True),
    ("director", "Directeur", "Direction", "Pilote la direction de l'etablissement.", "#1D4ED8", True),
    ("principal", "Proviseur", "Direction", "Supervise le secondaire et les decisions pedagogiques.", "#2563EB", True),
    ("department_head", "Responsable de Departement", "Direction", "Coordonne un departement ou une filiere.", "#4338CA", True),
    ("pedagogy_coordinator", "Coordinateur Pedagogique", "Direction", "Coordonne les activites pedagogiques.", "#0891B2", True),
    ("receptionist", "Receptionniste", "Personnel administratif", "Accueil et informations administratives.", "#64748B", True),
    ("cashier", "Comptable caisse", "Personnel administratif", "Encaissements et caisse.", "#16A34A", True),
    ("accountant", "Comptable", "Personnel administratif", "Comptabilite et rapports financiers.", "#15803D", True),
    ("secretary", "Secretaire", "Personnel administratif", "Secretariat et documents.", "#64748B", True),
    ("registrar", "Gestionnaire des admissions", "Personnel administratif", "Admissions, inscriptions et dossiers.", "#EA580C", True),
    ("educator", "Educateur", "Personnel academique", "Vie scolaire et suivi des eleves.", "#0D9488", True),
    ("teacher", "Professeur", "Personnel academique", "Enseignement, notes et presences.", "#9333EA", True),
    ("trainer", "Formateur", "Personnel academique", "Formation professionnelle et continue.", "#9333EA", True),
    ("instructor", "Enseignant", "Personnel academique", "Enseignement et evaluation.", "#9333EA", True),
    ("student", "Etudiant", "Utilisateurs finaux", "Acces portail et documents personnels.", "#475569", True),
    ("pupil", "Eleve", "Utilisateurs finaux", "Acces portail eleve.", "#475569", True),
    ("parent", "Parent/Tuteur", "Utilisateurs finaux", "Acces parent et suivi enfant.", "#475569", True),
    ("staff", "Personnel", "Personnel administratif", "Acces interne limite.", "#64748B", True),
]

CUSTOM_ROLE_EXAMPLES = [
    "responsable_informatique",
    "responsable_discipline",
    "bibliothecaire",
    "gestionnaire_transports",
    "responsable_internats",
    "responsable_stages",
    "responsable_laboratoire",
    "coordinateur_universitaire",
]

ALL_PERMISSIONS = [
    f"{module}:{action}"
    for module, _label, _category in PERMISSION_MODULES
    for action in STANDARD_ACTIONS
]

PERMISSIONS = {
    models.UserRole.SUPER_ADMIN: {"*"},
    models.UserRole.SCHOOL_ADMIN: {"*"},
    models.UserRole.ADMIN: {"*"},
    models.UserRole.DIRECTION: {
        "students:view", "students:create", "students:edit", "teachers:view", "teachers:edit",
        "finance_fees:view", "payments:view", "payments:edit", "payments:approve", "accounting:view",
        "classes:view", "classes:edit", "grades:view", "grades:approve", "report_cards:export",
        "operations:view", "operations:edit", "enterprise:view", "enterprise:edit", "enterprise:approve",
        "files:view", "files:download", "files:share", "settings:view", "audit:view", "security:view",
        "compliance:export", "monitoring:view", "backups:create",
    },
    models.UserRole.DIRECTOR: {
        "students:view", "teachers:view", "finance_fees:view", "payments:view", "accounting:view",
        "classes:view", "grades:view", "report_cards:view", "report_cards:export", "audit:view",
        "enterprise:view", "enterprise:approve", "messages:share", "notifications:share",
    },
    models.UserRole.PRINCIPAL: {
        "students:view", "students:edit", "teachers:view", "classes:view", "classes:edit",
        "grades:view", "grades:approve", "report_cards:view", "report_cards:print", "exams:approve",
    },
    models.UserRole.DEPARTMENT_HEAD: {"teachers:view", "classes:view", "subjects:view", "grades:view", "grades:approve", "timetable:view"},
    models.UserRole.PEDAGOGY_COORDINATOR: {"classes:view", "classes:edit", "subjects:view", "timetable:view", "timetable:edit", "grades:view", "report_cards:view"},
    models.UserRole.REGISTRAR: {
        "students:view", "students:create", "students:edit", "parents:view", "parents:create",
        "operations:view", "operations:create", "operations:edit", "files:view", "files:create", "files:download", "files:share",
        "report_cards:print",
    },
    models.UserRole.RECEPTIONIST: {"students:view", "parents:view", "messages:create", "notifications:view"},
    models.UserRole.SECRETARY: {"students:view", "teachers:view", "files:view", "files:create", "files:download", "files:share", "report_cards:print", "messages:create"},
    models.UserRole.CASHIER: {
        "students:view", "finance_fees:view", "payments:view", "payments:create", "receipts:print", "receipts:export", "accounting:view",
        "students:read", "finance:read", "finance:write", "reports:read", "documents:receipt", "files:read", "files:download",
    },
    models.UserRole.ACCOUNTANT: {"finance_fees:view", "invoices:view", "payments:view", "receipts:view", "expenses:view", "accounting:view", "accounting:export", "files:view", "files:create", "files:download", "files:share"},
    models.UserRole.TEACHER: {
        "students:view", "classes:view", "subjects:view", "timetable:view", "grades:view",
        "grades:create", "grades:edit", "report_cards:view", "files:view", "files:create", "files:download", "files:share",
    },
    models.UserRole.EDUCATOR: {"students:view", "students:edit", "classes:view", "messages:create", "notifications:create"},
    models.UserRole.TRAINER: {"students:view", "classes:view", "subjects:view", "grades:view", "grades:create", "files:view", "files:create", "files:download", "files:share"},
    models.UserRole.INSTRUCTOR: {"students:view", "classes:view", "subjects:view", "grades:view", "grades:create", "files:view", "files:create", "files:download", "files:share"},
    models.UserRole.PARENT: {"portal:view", "portal:create", "files:view", "files:create", "files:download", "payments:view"},
    models.UserRole.STUDENT: {"portal:view", "portal:create", "files:view", "files:create", "files:download", "grades:view", "timetable:view"},
    models.UserRole.PUPIL: {"portal:view", "files:view", "files:download", "grades:view", "timetable:view"},
    models.UserRole.STAFF: {"portal:view"},
}

PRODUCTION_PERMISSIONS = {
    "audit:view",
    "backups:create",
    "compliance:delete",
    "compliance:export",
    "enterprise:approve",
    "files:delete",
    "files:view",
    "files:create",
    "monitoring:view",
    "security:view",
    "roles:manage_settings",
    "users:manage_settings",
}

LEGACY_PERMISSION_CATALOG = {
    f"{module}:{action}"
    for module in LEGACY_ALIASES
    for action in ["read", "write", "approve", "export", "delete", "issue", "receipt", "run", "erase"]
}


def permission_catalog() -> list[str]:
    catalog = set(ALL_PERMISSIONS)
    catalog.update(PRODUCTION_PERMISSIONS)
    catalog.update(LEGACY_PERMISSION_CATALOG)
    for values in PERMISSIONS.values():
        catalog.update(value for value in values if value != "*")
    return sorted(catalog)


def permission_modules() -> list[dict]:
    return [
        {"key": key, "label": label, "category": category, "actions": STANDARD_ACTIONS}
        for key, label, category in PERMISSION_MODULES
    ]


def default_role_definitions() -> list[dict]:
    return [
        {
            "key": key,
            "name": name,
            "category": category,
            "description": description,
            "color": color,
            "is_system": is_system,
            "is_active": True,
            "parent_role_key": None,
        }
        for key, name, category, description, color, is_system in DEFAULT_ROLE_DEFINITIONS
    ]


def _normalize_permission(permission: str) -> str:
    if ":" not in permission:
        return permission
    module, action = permission.split(":", 1)
    module = LEGACY_ALIASES.get(module, [module])[0]
    action = ACTION_ALIASES.get(action, action)
    return f"{module}:{action}"


def _legacy_matches(user_permissions: set[str], permission: str) -> bool:
    if ":" not in permission:
        return permission in user_permissions
    module, action = permission.split(":", 1)
    normalized_action = ACTION_ALIASES.get(action, action)
    modules = LEGACY_ALIASES.get(module, [module])
    for candidate_module in modules:
        if f"{candidate_module}:{normalized_action}" in user_permissions:
            return True
        if f"{candidate_module}:full_access" in user_permissions:
            return True
    return False


def _role_matrix_permissions(role_key: str, school_id: Optional[int], db: Optional[Session]) -> tuple[set[str], set[str]]:
    if not db:
        return set(), set()
    rows = db.query(models.RolePermissionMatrix).filter(
        models.RolePermissionMatrix.role_key == role_key,
        models.RolePermissionMatrix.school_id == school_id,
    ).all()
    enabled = {row.permission for row in rows if row.is_enabled}
    disabled = {row.permission for row in rows if not row.is_enabled}
    return enabled, disabled


def _legacy_role_permissions(role_key: str, school_id: Optional[int], db: Optional[Session]) -> tuple[set[str], set[str]]:
    if not db:
        return set(), set()
    try:
        enum_role = models.UserRole(role_key)
    except ValueError:
        return set(), set()
    rows = db.query(models.RolePermission).filter(
        models.RolePermission.role == enum_role,
        models.RolePermission.school_id == school_id,
    ).all()
    enabled = {row.permission for row in rows if row.is_enabled}
    disabled = {row.permission for row in rows if not row.is_enabled}
    return enabled, disabled


def _assigned_role_keys(user: models.User, db: Optional[Session]) -> set[str]:
    keys = {user.role.value}
    if not db:
        return keys
    rows = db.query(models.UserRoleAssignment).filter(
        models.UserRoleAssignment.user_id == user.id,
        models.UserRoleAssignment.school_id == user.school_id,
    ).all()
    keys.update(row.role_key for row in rows)
    return keys


def effective_permissions(user: models.User, db: Optional[Session] = None) -> set[str]:
    user_permissions: set[str] = set()
    disabled_permissions: set[str] = set()
    for role_key in _assigned_role_keys(user, db):
        enum_role = None
        try:
            enum_role = models.UserRole(role_key)
        except ValueError:
            enum_role = None
        role_permissions = set(PERMISSIONS.get(enum_role, set())) if enum_role else set()
        if "*" in role_permissions:
            role_permissions = set(permission_catalog())
            role_permissions.add("*")
        enabled, disabled = _role_matrix_permissions(role_key, user.school_id, db)
        legacy_enabled, legacy_disabled = _legacy_role_permissions(role_key, user.school_id, db)
        user_permissions.update(role_permissions)
        user_permissions.update(enabled)
        user_permissions.update(legacy_enabled)
        disabled_permissions.update(disabled)
        disabled_permissions.update(legacy_disabled)
    user_permissions.difference_update(disabled_permissions)
    return {_normalize_permission(permission) if permission != "*" else permission for permission in user_permissions}


def has_permission(user: models.User, permission: str, db: Optional[Session] = None) -> bool:
    user_permissions = effective_permissions(user, db)
    return "*" in user_permissions or _legacy_matches(user_permissions, permission)


def require_permission(user: models.User, permission: str, db: Optional[Session] = None) -> None:
    if not has_permission(user, permission, db):
        raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")


def permission_snapshot(user: models.User, db: Optional[Session] = None) -> dict:
    effective = sorted(effective_permissions(user, db))
    return {"role": user.role.value, "roles": sorted(_assigned_role_keys(user, db)), "permissions": effective}


def role_permission_snapshot(role: models.UserRole, school_id: Optional[int], db: Session) -> dict:
    return role_key_permission_snapshot(role.value, school_id, db)


def role_key_permission_snapshot(role_key: str, school_id: Optional[int], db: Session) -> dict:
    enum_role = None
    try:
        enum_role = models.UserRole(role_key)
    except ValueError:
        enum_role = None
    base = set(PERMISSIONS.get(enum_role, set())) if enum_role else set()
    if "*" in base:
        base = set(permission_catalog())
        base.add("*")
    enabled, disabled = _role_matrix_permissions(role_key, school_id, db)
    legacy_enabled, legacy_disabled = _legacy_role_permissions(role_key, school_id, db)
    enabled.update(legacy_enabled)
    disabled.update(legacy_disabled)
    effective = (base | enabled) - disabled
    return {
        "role": role_key,
        "school_id": school_id,
        "base_permissions": sorted(base),
        "enabled_permissions": sorted(effective),
        "disabled_permissions": sorted(disabled),
        "available_permissions": permission_catalog(),
    }
