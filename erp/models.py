# erp/models.py
from __future__ import annotations

import typing as _t
from datetime import datetime

from erp.extensions import db

# ──────────────────────────────────────────────────────────────────────────────
# Optional Postgres JSONB; gracefully fall back to generic JSON if unavailable
# ──────────────────────────────────────────────────────────────────────────────
try:
    from sqlalchemy.dialects.postgresql import JSONB as _JSON
except Exception:  # pragma: no cover
    _JSON = db.JSON  # works on any DB; on Postgres use JSONB
# -----------------------------------------------------------------------------

# ──────────────────────────────────────────────────────────────────────────────
# Role/User mixins: use Flask-Security if present; otherwise use our shim
# ──────────────────────────────────────────────────────────────────────────────
try:
    # If you later add Flask-Security-Too this will automatically use it
    from flask_security import RoleMixin, UserMixin  # type: ignore
except Exception:  # pragma: no cover
    from erp.security_shim import RoleMixin, UserMixin


# ──────────────────────────────────────────────────────────────────────────────
# Naming convention helps Alembic autogenerate deterministic constraint names
# ──────────────────────────────────────────────────────────────────────────────
# If you already set metadata naming convention elsewhere, you can remove this.
# Flask-SQLAlchemy 3.x exposes metadata via db.metadata
db.metadata.naming_convention.update({
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})


# ──────────────────────────────────────────────────────────────────────────────
# Small mixins
# ──────────────────────────────────────────────────────────────────────────────
class SurrogatePK:
    id = db.Column(db.Integer, primary_key=True)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(),
                           onupdate=db.func.now(), nullable=False)


# ──────────────────────────────────────────────────────────────────────────────
# Association tables
# ──────────────────────────────────────────────────────────────────────────────
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


# ──────────────────────────────────────────────────────────────────────────────
# Role / User
# ──────────────────────────────────────────────────────────────────────────────
class Role(SurrogatePK, TimestampMixin, RoleMixin, db.Model):
    __tablename__ = "roles"

    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    # Optional: store a JSON/CSV of permissions if you use them
    permissions_ = db.Column(db.Text)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role {self.id} {self.name!r}>"


class User(SurrogatePK, TimestampMixin, UserMixin, db.Model):
    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    # Store a hash, not a raw password. Field name is generic to avoid coupling.
    password_hash = db.Column(db.String(255))
    active = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))
    mfa_enabled = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))

    # Profile-ish fields (optional; safe defaults)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    last_login_at = db.Column(db.DateTime(timezone=True))

    # Many-to-many roles
    roles = db.relationship(
        "Role",
        secondary=user_roles,
        backref=db.backref("users", lazy="dynamic"),
        lazy="selectin",
    )

    # Dashboards (one-to-many)
    dashboards = db.relationship(
        "UserDashboard",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.id} {self.email!r}>"


# ──────────────────────────────────────────────────────────────────────────────
# Token blocklist (useful for JWT revocation) – optional but common
# ──────────────────────────────────────────────────────────────────────────────
class TokenBlocklist(SurrogatePK, db.Model):
    __tablename__ = "token_blocklist"

    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TokenBlocklist jti={self.jti!r}>"


# ──────────────────────────────────────────────────────────────────────────────
# User dashboard customization referenced by routes/dashboard_customize.py
# ──────────────────────────────────────────────────────────────────────────────
class UserDashboard(SurrogatePK, TimestampMixin, db.Model):
    __tablename__ = "user_dashboards"
    __table_args__ = (
        # Enforce uniqueness of (user_id, name) so each user can have named layouts
        db.UniqueConstraint("user_id", "name", name="uq_user_dashboards_user_name"),
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, server_default=db.text("'default'"))
    # Arbitrary layout configuration (e.g., list of widgets with sizes/positions)
    layout = db.Column(_JSON, nullable=False, server_default=db.text("'[]'"))
    # Optional filters or settings associated with this dashboard
    settings = db.Column(_JSON, nullable=False, server_default=db.text("'{}'"))

    user = db.relationship("User", back_populates="dashboards", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserDashboard {self.id} user={self.user_id} name={self.name!r}>"


# ──────────────────────────────────────────────────────────────────────────────
# Helper: convenient typed export (optional)
# ──────────────────────────────────────────────────────────────────────────────
__all__ = [
    "db",
    "Role",
    "User",
    "TokenBlocklist",
    "UserDashboard",
    "user_roles",
]
