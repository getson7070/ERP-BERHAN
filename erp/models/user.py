"""User model and Flask-Login integration for ERP-BERHAN."""

from __future__ import annotations

from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from erp.extensions import db


class User(UserMixin, db.Model):
    """Application user used for authentication."""

    __tablename__ = "users"
    __table_args__ = (
        db.UniqueConstraint("org_id", "telegram_chat_id", name="uq_users_org_chat"),
    )

    # NOTE: This schema is aligned with your current DB table:
    # id | username | email | password_hash | created_at | updated_at
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        default=1,
        server_default="1",
        index=True,
    )
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    telegram_chat_id = db.Column(db.String(128), nullable=True, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    roles = db.relationship(
        "Role",
        secondary="user_role_assignments",
        backref="users",
        lazy="select",
    )

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # ------------------------------------------------------------------
    # Password helpers – compatible with your existing admin hash
    # (pbkdf2:sha256 via Werkzeug generate_password_hash).
    # ------------------------------------------------------------------

    @property
    def password(self) -> None:
        """Write-only password property."""
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, raw: str) -> None:
        # Force the same algorithm you used manually:
        self.password_hash = generate_password_hash(raw, method="pbkdf2:sha256")

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    # Backwards-compatible name if older code expects verify_password
    def verify_password(self, raw: str) -> bool:
        return self.check_password(raw)

    # ------------------------------------------------------------------
    # Flask-Login integration
    # ------------------------------------------------------------------

    def get_id(self) -> str:
        # Explicit string cast – Flask-Login stores IDs as strings in session
        return str(self.id)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username!r} email={self.email!r}>"


