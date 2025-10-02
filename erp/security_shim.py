# erp/security_shim.py
from __future__ import annotations

class RoleMixin:
    """Minimal stand-in for flask_security RoleMixin."""
    @property
    def rolename(self):
        return getattr(self, "name", None)

class UserMixin:
    """Minimal stand-in for flask_security UserMixin."""
    @property
    def is_active(self) -> bool:   # for parity with many auth libs
        return True

    @property
    def is_authenticated(self) -> bool:
        return True

    def has_role(self, name: str) -> bool:
        roles = getattr(self, "roles", []) or []
        for r in roles:
            if getattr(r, "name", None) == name:
                return True
        return False
