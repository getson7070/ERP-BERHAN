"""Database models for core ERP entities."""

from datetime import datetime
from decimal import Decimal

from flask_security import RoleMixin, UserMixin

from .extensions import db

# Association table for many-to-many user/role relationship
roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("users.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("roles.id")),
)


class Inventory(db.Model):  # type: ignore[name-defined]
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self) -> str:  # pragma: no cover - repr is for debugging
        return f"<Inventory {self.name}={self.quantity}>"


class Invoice(db.Model):  # type: ignore[name-defined]
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    number = db.Column(db.String(64), unique=True, nullable=False)
    total = db.Column(db.Numeric(scale=2), nullable=False, default=Decimal("0.00"))
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delete_after = db.Column(db.DateTime)

    def __repr__(self) -> str:  # pragma: no cover - repr is for debugging
        return f"<Invoice {self.number} total={self.total}>"


class Role(db.Model, RoleMixin):  # type: ignore[name-defined]
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):  # type: ignore[name-defined]
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), default=True)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    mfa_secret = db.Column(db.String(32))
    anonymized = db.Column(db.Boolean, default=False, nullable=False)
    roles = db.relationship(
        "Role",
        secondary=roles_users,
        backref=db.backref("users", lazy="dynamic"),
    )  # type: ignore[assignment]


class DataLineage(db.Model):  # type: ignore[name-defined]
    __tablename__ = "data_lineage"

    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(128), nullable=False)
    column_name = db.Column(db.String(128), nullable=False)
    source = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class UserDashboard(db.Model):  # type: ignore[name-defined]
    """Persist user-specific dashboard layouts."""

    __tablename__ = "user_dashboards"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True
    )
    layout = db.Column(db.Text, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
