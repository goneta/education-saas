from fastapi import HTTPException

from . import models


PERMISSIONS = {
    models.UserRole.SUPER_ADMIN: {"*"},
    models.UserRole.SCHOOL_ADMIN: {"*"},
    models.UserRole.DIRECTION: {
        "students:read", "students:write", "teachers:read", "teachers:write",
        "finance:read", "finance:write", "finance:approve", "pedagogy:read", "pedagogy:write",
        "operations:read", "operations:write", "enterprise:read", "enterprise:write",
        "reports:read", "documents:issue", "settings:read",
    },
    models.UserRole.REGISTRAR: {
        "students:read", "students:write", "teachers:read",
        "pedagogy:read", "operations:read", "operations:write",
        "documents:issue", "reports:read",
    },
    models.UserRole.CASHIER: {
        "students:read", "finance:read", "finance:write", "reports:read", "documents:receipt",
    },
    models.UserRole.TEACHER: {
        "students:read", "pedagogy:read", "pedagogy:write", "grades:write", "attendance:write",
    },
    models.UserRole.PARENT: {"portal:read", "portal:write"},
    models.UserRole.STUDENT: {"portal:read", "portal:write"},
    models.UserRole.STAFF: {"portal:read"},
}


def has_permission(user: models.User, permission: str) -> bool:
    user_permissions = PERMISSIONS.get(user.role, set())
    return "*" in user_permissions or permission in user_permissions


def require_permission(user: models.User, permission: str) -> None:
    if not has_permission(user, permission):
        raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")


def permission_snapshot(user: models.User) -> dict:
    permissions = PERMISSIONS.get(user.role, set())
    if "*" in permissions:
        effective = sorted({perm for values in PERMISSIONS.values() for perm in values if perm != "*"})
        effective.append("*")
    else:
        effective = sorted(permissions)
    return {"role": user.role.value, "permissions": effective}
