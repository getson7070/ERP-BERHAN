# erp/models.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db
from .security_shim import RoleMixin, UserMixin


# ───────────────────────────── Base mixins ────────────────────────────────────
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class PKMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


# ───────────────────── Association table: users ↔ roles ───────────────────────
users_roles = db.Table(
    "users_roles",
    db.metadata,
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


# ─────────────────────────────── Role model ───────────────────────────────────
class Role(db.Model, PKMixin, TimestampMixin, RoleMixin):
    __tablename__ = "roles"

    # Simple role model (compatible with RoleMixin shim)
    name: Mapped[str] = mapped_column(db.String(80), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(db.String(255))

    def __repr__(self) -> str:
        return f"<Role {self.name!r}>"


# ─────────────────────────────── User model ───────────────────────────────────
class User(db.Model, PKMixin, TimestampMixin, UserMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    email: Mapped[str] = mapped_column(db.String(255), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(db.String(255))
    active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    # Optional flags/fields that many apps expect
    first_name: Mapped[Optional[str]] = mapped_column(db.String(80))
    last_name: Mapped[Optional[str]] = mapped_column(db.String(80))
    mfa_enabled: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    # Relations
    roles = relationship(
        "Role",
        secondary=users_roles,
        backref=db.backref("users", lazy="dynamic"),
        lazy="selectin",
    )

    dashboards = relationship(
        "UserDashboard",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.email!r}>"

    # Convenience helpers used by some views
    @property
    def full_name(self) -> str:
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(p for p in parts if p).strip() or self.email

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "active": self.active,
            "mfa_enabled": self.mfa_enabled,
            "roles": [r.name for r in self.roles] if self.roles else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ─────────────────────────── UserDashboard model ──────────────────────────────
class UserDashboard(db.Model, PKMixin, TimestampMixin):
    """
    Stores per-user dashboard layout/config. Your route `dashboard_customize.py`
    imports `UserDashboard` and `db`.
    """
    __tablename__ = "user_dashboards"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_dashboards_user_name"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(db.String(120), nullable=False, index=True)

    # Layout/config payload. Use JSON to keep it flexible.
    layout: Mapped[Optional[dict]] = mapped_column(db.JSON)

    # Relationship back to User
    user = relationship("User", back_populates="dashboards", lazy="joined")

    def __repr__(self) -> str:
        return f"<UserDashboard user={self.user_id} name={self.name!r}>"


# ─────────────────────────── export convenience ───────────────────────────────
__all__ = [
    "db",
    "User",
    "Role",
    "UserDashboard",
    "users_roles",
]
