from __future__ import annotations

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, index=True)  # admin|employee|client
    username = db.Column(db.String(64), unique=True, index=True, nullable=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    mac_address = db.Column(db.String(64), nullable=True)       # for employees
    otp_secret = db.Column(db.String(32), nullable=True)        # for admins (optional)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} role={self.role} username={self.username!r}>"
