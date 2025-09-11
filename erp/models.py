"""Database models for core ERP entities."""

from datetime import datetime, timedelta, UTC
from decimal import Decimal

from flask_security import RoleMixin, UserMixin

from .extensions import db
from .tenant import TenantMixin

# Association table for many-to-many user/role relationship
roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("users.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("roles.id")),
)


class Inventory(TenantMixin, db.Model):  # type: ignore[name-defined]
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    sku = db.Column(db.String(64), nullable=False, unique=True, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self) -> str:  # pragma: no cover - repr is for debugging
        return f"<Inventory {self.name}={self.quantity}>"


class Invoice(TenantMixin, db.Model):  # type: ignore[name-defined]
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    number = db.Column(db.String(64), unique=True, nullable=False)
    total = db.Column(db.Numeric(scale=2), nullable=False, default=Decimal("0.00"))
    issued_at = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
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
    retain_until = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC) + timedelta(days=365 * 7),
    )
    roles = db.relationship(
        "Role",
        secondary=roles_users,
        backref=db.backref("users", lazy="dynamic"),
    )  # type: ignore[assignment]


class Organization(db.Model):  # type: ignore[name-defined]
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)


class DataLineage(db.Model):  # type: ignore[name-defined]
    __tablename__ = "data_lineage"

    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(128), nullable=False)
    column_name = db.Column(db.String(128), nullable=False)
    source = db.Column(db.String(256), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )


class UserDashboard(db.Model):  # type: ignore[name-defined]
    """Persist user-specific dashboard layouts."""

    __tablename__ = "user_dashboards"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True
    )
    layout = db.Column(db.Text, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class Employee(TenantMixin, db.Model):  # type: ignore[name-defined]
    __tablename__ = "hr_employees"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint("org_id", "name", name="uq_hr_employees_org_name"),
    )


class Recruitment(TenantMixin, db.Model):  # type: ignore[name-defined]
    __tablename__ = "hr_recruitment"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(120), nullable=False)
    applied_on = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )
    status = db.Column(db.String(20), nullable=False, default="applied", index=True)

    __table_args__ = (
        db.UniqueConstraint(
            "org_id", "candidate_name", "position", name="uq_hr_recruitment_candidate"
        ),
        db.CheckConstraint(
            "status in ('applied','shortlisted','approved')",
            name="chk_hr_recruitment_status",
        ),
    )


class PerformanceReview(TenantMixin, db.Model):  # type: ignore[name-defined]
    __tablename__ = "hr_performance_reviews"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_name = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    review_date = db.Column(
        db.DateTime, default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        db.CheckConstraint("score >= 1 AND score <= 5", name="chk_performance_score"),
        db.UniqueConstraint(
            "org_id", "employee_name", "review_date", name="uq_hr_performance_once"
        ),
    )


db.Index(
    "ix_hr_recruitment_pending",
    Recruitment.org_id,
    Recruitment.status,
    postgresql_where=db.text("status != 'approved'"),
)
db.Index("ix_hr_performance_reviews_review_date", PerformanceReview.review_date)
