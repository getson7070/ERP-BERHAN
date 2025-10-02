# erp/security_shim.py
# Minimal stand-ins for Flask-Security RoleMixin/UserMixin to avoid external dependency.

class RoleMixin:
    @property
    def permissions(self):
        # adjust if your Role model uses a different field name
        return getattr(self, "permissions_", None)

    def get_id(self):
        return getattr(self, "id", None)

    def __str__(self):
        return getattr(self, "name", super().__str__())


class UserMixin:
    @property
    def is_active(self):
        return getattr(self, "active", True)

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def get_id(self):
        return getattr(self, "id", None)
