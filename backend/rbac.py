from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models


PERMISSIONS = {
    models.UserRole.SUPER_ADMIN: {"*"},
    models.UserRole.SCHOOL_ADMIN: {"*"},
    models.UserRole.DIRECTION: {
        "students:read", "students:write", "teachers:read", "teachers:write",
        "finance:read", "finance:write", "finance:approve", "pedagogy:read", "pedagogy:write",
        "operations:read", "operations:write", "enterprise:read", "enterprise:write",
        "enterprise:approve", "files:read", "files:write", "files:delete",
        "reports:read", "documents:issue", "settings:read",
        "settings:write", "audit:read", "security:read", "compliance:export", "monitoring:read",
        "compliance:erase", "backup:run",
    },
    models.UserRole.REGISTRAR: {
        "students:read", "students:write", "teachers:read",
        "pedagogy:read", "operations:read", "operations:write",
        "documents:issue", "reports:read", "files:read", "files:write",
    },
    models.UserRole.CASHIER: {
        "students:read", "finance:read", "finance:write", "reports:read", "documents:receipt", "files:read",
    },
    models.UserRole.TEACHER: {
        "students:read", "pedagogy:read", "pedagogy:write", "grades:write", "attendance:write", "files:read", "files:write",
    },
    models.UserRole.PARENT: {"portal:read", "portal:write", "files:read", "files:write"},
    models.UserRole.STUDENT: {"portal:read", "portal:write", "files:read", "files:write"},
    models.UserRole.STAFF: {"portal:read"},
}

PRODUCTION_PERMISSIONS = {
    "audit:read",
    "backup:run",
    "compliance:erase",
    "compliance:export",
    "enterprise:approve",
    "files:delete",
    "files:read",
    "files:write",
    "monitoring:read",
    "security:read",
}


def permission_catalog() -> list[str]:
    catalog = {perm for values in PERMISSIONS.values() for perm in values if perm != "*"}
    catalog.update(PRODUCTION_PERMISSIONS)
    return sorted(catalog)


def _db_overrides(user: models.User, db: Optional[Session]) -> tuple[set[str], set[str]]:
    if not db or not user.school_id:
        return set(), set()
    rows = db.query(models.RolePermission).filter(
        models.RolePermission.role == user.role,
        models.RolePermission.school_id == user.school_id,
    ).all()
    enabled = {row.permission for row in rows if row.is_enabled}
    disabled = {row.permission for row in rows if not row.is_enabled}
    return enabled, disabled


def effective_permissions(user: models.User, db: Optional[Session] = None) -> set[str]:
    user_permissions = set(PERMISSIONS.get(user.role, set()))
    enabled, disabled = _db_overrides(user, db)
    if "*" in user_permissions:
        user_permissions = set(permission_catalog())
        user_permissions.add("*")
    user_permissions.update(enabled)
    user_permissions.difference_update(disabled)
    return user_permissions


def has_permission(user: models.User, permission: str, db: Optional[Session] = None) -> bool:
    user_permissions = effective_permissions(user, db)
    return "*" in user_permissions or permission in user_permissions


def require_permission(user: models.User, permission: str, db: Optional[Session] = None) -> None:
    if not has_permission(user, permission, db):
        raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")


def permission_snapshot(user: models.User, db: Optional[Session] = None) -> dict:
    effective = sorted(effective_permissions(user, db))
    return {"role": user.role.value, "permissions": effective}


def role_permission_snapshot(role: models.UserRole, school_id: Optional[int], db: Session) -> dict:
    base = set(PERMISSIONS.get(role, set()))
    if "*" in base:
        base = set(permission_catalog())
        base.add("*")
    rows = db.query(models.RolePermission).filter(
        models.RolePermission.role == role,
        models.RolePermission.school_id == school_id,
    ).all()
    enabled = {row.permission for row in rows if row.is_enabled}
    disabled = {row.permission for row in rows if not row.is_enabled}
    effective = (base | enabled) - disabled
    return {
        "role": role,
        "school_id": school_id,
        "base_permissions": sorted(base),
        "enabled_permissions": sorted(effective),
        "disabled_permissions": sorted(disabled),
        "available_permissions": permission_catalog(),
    }
