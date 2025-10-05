# erp/models.py
from __future__ import annotations
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import func
from .extensions import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, index=True)      # 'admin' | 'employee' | 'client'
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Security extras
    mac_address = db.Column(db.String(32), index=True)               # required for employees
    otp_secret = db.Column(db.String(32))                             # optional for admins (TOTP)

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=func.now())

    def set_password(self, pw: str) -> None:
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        return check_password_hash(self.password_hash, pw)

    def get_id(self) -> str:  # flask_login
        return str(self.id)
