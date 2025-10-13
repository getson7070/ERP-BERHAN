# erp/models/employee.py
from __future__ import annotations
from . import db  # imported from erp.extensions via erp/models/__init__.py

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(50))
    title = db.Column(db.String(120))
    department = db.Column(db.String(120))

    # keep status simple and portable (string + check constraint in migration)
    status = db.Column(db.String(32), nullable=False, default="active")
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    hired_at = db.Column(db.Date)
    terminated_at = db.Column(db.Date)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def __repr__(self) -> str:
        return f"<Employee id={self.id} {self.full_name} {self.email}>"
