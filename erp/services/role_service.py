from __future__ import annotations

from erp.extensions import db
from erp.models import Role, User, UserRoleAssignment
from erp.security import user_has_role, _get_user_role_names


def _ensure_role(role_name: str) -> Role:
    role = Role.query.filter(Role.name.ilike(role_name)).first()
    if role is None:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.flush()
    return role


def grant_role_to_user(
    *, org_id: int | None, user_id: int, role_key: str, acting_user: User | None = None
) -> None:
    normalized = role_key.strip().lower()
    if normalized == "superadmin" and acting_user and not user_has_role(acting_user, "superadmin"):
        raise PermissionError("only superadmins can grant superadmin")

    user = User.query.get(user_id)
    if user is None:
        raise ValueError("user not found")

    role = _ensure_role(normalized)
    if not UserRoleAssignment.query.filter_by(user_id=user.id, role_id=role.id).first():
        db.session.add(UserRoleAssignment(user_id=user.id, role_id=role.id))
    db.session.commit()


def revoke_role_from_user(
    *, org_id: int | None, user_id: int, role_key: str, acting_user: User | None = None
) -> None:
    normalized = role_key.strip().lower()
    user = User.query.get(user_id)
    if user is None:
        raise ValueError("user not found")

    role = Role.query.filter(Role.name.ilike(normalized)).first()
    if role is None:
        return

    if normalized == "admin" and acting_user and not user_has_role(acting_user, "superadmin"):
        admin_count = (
            db.session.query(UserRoleAssignment)
            .join(Role, Role.id == UserRoleAssignment.role_id)
            .filter(Role.name.ilike("admin"))
            .count()
        )
        if admin_count <= 1:
            raise PermissionError("cannot revoke last admin")

    UserRoleAssignment.query.filter_by(user_id=user.id, role_id=role.id).delete()
    db.session.commit()


def list_role_names(user: User | None) -> set[str]:
    return _get_user_role_names(user)
