# erp/models.py
from __future__ import annotations
from datetime import datetime, timedelta
import secrets
from typing import Optional, List

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, func

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(64), nullable=False, default="employee", index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # MFA
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    mfa_secret = db.Column(db.String(64), nullable=True)            # hex secret
    mfa_recovery = db.Column(db.Text, nullable=True)                # comma-separated hashed codes

    # Auth hygiene / brute force protection
    failed_logins = db.Column(db.Integer, default=0, nullable=False)
    last_failed_at = db.Column(db.DateTime, nullable=True)
    locked_until = db.Column(db.DateTime, nullable=True)

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    def enable_mfa(self) -> None:
        self.mfa_enabled = True
        self.mfa_secret = secrets.token_hex(16)
        # generate 8 recovery codes (hashed) – shown once to user at enrollment
        codes = [secrets.token_hex(4) for _ in range(8)]
        self.mfa_recovery = ",".join(generate_password_hash(c) for c in codes)
        self._pending_plain_recovery_codes = codes  # transient, not persisted

    def get_pending_recovery_codes(self) -> Optional[List[str]]:
        return getattr(self, "_pending_plain_recovery_codes", None)

    def verify_mfa_token(self, token: str) -> bool:
        if not self.mfa_enabled:
            return True
        if not self.mfa_secret:
            return False
        # prefer pyotp TOTP if available, else fall back to recovery
        try:
            import pyotp
            totp = pyotp.TOTP(self.mfa_secret)
            if totp.verify(token, valid_window=1):
                return True
        except Exception:
            pass
        # recovery codes
        if self.mfa_recovery:
            parts = [p.strip() for p in self.mfa_recovery.split(",") if p.strip()]
            for i, ph in enumerate(parts):
                if check_password_hash(ph, token):
                    # burn one-time recovery code
                    parts.pop(i)
                    self.mfa_recovery = ",".join(parts)
                    return True
        return False

    def register_failed_login(self) -> None:
        self.failed_logins += 1
        self.last_failed_at = datetime.utcnow()
        if self.failed_logins >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)

    def reset_failed_logins(self) -> None:
        self.failed_logins = 0
        self.last_failed_at = None
        self.locked_until = None

    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > datetime.utcnow()

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

# Helpful indexes for reporting and filters
Index("ix_users_created_at", User.created_at)
Index("ix_users_role_active", User.role, User.is_active)
