"""Employee directory model scoped to an organisation."""

from datetime import UTC, datetime

from erp.models import db  # re-exported from erp.models.__init__


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    phone = db.Column(db.String(50))
    role = db.Column(db.String(120), default="staff")
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    @classmethod
    def tenant_query(cls, org_id: int | None = None):
        """Convenience helper to scope queries by organisation."""

        query = cls.query
        if org_id is not None:
            query = query.filter_by(organization_id=org_id)
        return query

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Employee {self.id} {self.email}>"





