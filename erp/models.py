# erp/models.py
from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

class Role(str, Enum):
    CLIENT = "client"
    EMPLOYEE = "employee"
    ADMIN = "admin"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role, native_enum=False), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # MFA (already present in your migrations)
    mfa_secret = db.Column(db.String(64))
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)  # pbkdf2:sha256

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

class DeviceAuthorization(db.Model):
    """
    Allow-list of hardware IDs permitted to log in.
    If you already have a similar table, keep it; just ensure uniqueness and FK.
    """
    __tablename__ = "device_authorizations"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    allowed = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("device_id", "user_id", name="uq_device_user"),
    )
