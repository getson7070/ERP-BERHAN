"""Client authentication models: accounts, password reset, OAuth links.

Important:
- Client accounts are distinct from employee/admin User accounts.
- Client accounts link to Institution (TIN-unique) via institution_id.
- Multiple client contacts per Institution are supported.
"""

from __future__ import annotations

from datetime import datetime, UTC, timedelta
import hashlib
import secrets
from uuid import uuid4

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from erp.extensions import db


class ClientAccount(UserMixin, db.Model):
    """Login-capable account for external clients."""

    __tablename__ = "client_accounts"
    __table_args__ = (
        db.Index("ix_client_accounts_org_email", "org_id", "email"),
        db.UniqueConstraint("org_id", "email", name="uq_client_accounts_org_email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), nullable=False, unique=True, index=True, default=lambda: str(uuid4()))

    org_id = db.Column(db.Integer, nullable=False, index=True)

    # Link to Institution (TIN-unique per org). Enables multi-contact per TIN.
    institution_id = db.Column(db.Integer, db.ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)

    # A stable external identifier if you later integrate to a CRM or ERP client id.
    client_id = db.Column(db.Integer, nullable=True, index=True)

    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(64), nullable=True)

    contact_name = db.Column(db.String(255), nullable=True)
    contact_position = db.Column(db.String(128), nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def get_id(self) -> str:
        return str(self.id)

    @property
    def roles(self):
        # Policy engine expects roles on current_user.
        return ["client"]

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class ClientPasswordReset(db.Model):
    """Password reset tokens for client accounts."""

    __tablename__ = "client_password_resets"
    __table_args__ = (db.Index("ix_client_password_resets_org_account", "org_id", "client_account_id"),)

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), nullable=False, unique=True, index=True, default=lambda: str(uuid4()))

    org_id = db.Column(db.Integer, nullable=False, index=True)
    client_account_id = db.Column(db.Integer, db.ForeignKey("client_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    token_hash = db.Column(db.String(64), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def issue(cls, org_id: int, client_account_id: int, ttl_minutes: int = 30) -> tuple["ClientPasswordReset", str]:
        token = secrets.token_urlsafe(32)
        rec = cls(
            org_id=org_id,
            client_account_id=client_account_id,
            token_hash=cls._hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(minutes=ttl_minutes),
        )
        return rec, token

    def is_valid(self, token: str) -> bool:
        if self.used_at is not None:
            return False
        if self.expires_at < datetime.now(UTC):
            return False
        return self.token_hash == self._hash_token(token)


class ClientOAuthAccount(db.Model):
    """Optional OAuth linkage for client accounts (e.g., Google)."""

    __tablename__ = "client_oauth_accounts"
    __table_args__ = (
        db.Index("ix_client_oauth_accounts_org_provider", "org_id", "provider"),
        db.UniqueConstraint("org_id", "provider", "provider_sub", name="uq_client_oauth_provider_sub"),
    )

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), nullable=False, unique=True, index=True, default=lambda: str(uuid4()))

    org_id = db.Column(db.Integer, nullable=False, index=True)
    client_account_id = db.Column(db.Integer, db.ForeignKey("client_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    provider = db.Column(db.String(32), nullable=False)          # e.g., "google"
    provider_sub = db.Column(db.String(255), nullable=False)     # subject identifier
    email = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
