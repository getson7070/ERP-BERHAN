from __future__ import annotations

from datetime import datetime
import hashlib
import secrets

from sqlalchemy import UniqueConstraint, func

from erp.extensions import db


class UserMFA(db.Model):
    __tablename__ = "user_mfa"
    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_user_mfa"),)

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)

    totp_secret = db.Column(db.String(64), nullable=True)
    is_enabled = db.Column(db.Boolean, nullable=False, default=False, index=True)

    enrolled_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())


class UserMFABackupCode(db.Model):
    __tablename__ = "user_mfa_backup_codes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)

    code_hash = db.Column(db.String(128), nullable=False, index=True)
    used_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    @staticmethod
    def make_code() -> str:
        return secrets.token_hex(4)

    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()


class UserSession(db.Model):
    __tablename__ = "user_sessions"
    __table_args__ = (UniqueConstraint("org_id", "session_id", name="uq_session_id"),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    org_id = db.Column(db.Integer, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)

    session_id = db.Column(db.String(128), nullable=False, index=True)

    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    last_seen_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked_by_id = db.Column(db.Integer, nullable=True)

    def mark_seen(self) -> None:
        self.last_seen_at = datetime.utcnow()

