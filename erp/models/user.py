from __future__ import annotations
from datetime import datetime
from erp.db import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # Optional org linkage (tests often create both)
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )

    role = db.Column(db.String(50), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization = db.relationship(
        "Organization",
        backref=db.backref("users", lazy=True, cascade="all, delete-orphan"),
        foreign_keys=[organization_id],
    )

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email!r} role={self.role}>"
