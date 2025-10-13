# erp/models/employee.py
from datetime import datetime
from . import db  # re-exported from erp.models.__init__

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    phone = db.Column(db.String(50))
    role = db.Column(db.String(120), default="staff")
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Employee {self.id} {self.email}>"
