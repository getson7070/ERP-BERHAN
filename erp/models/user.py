"""User model and Flask-Login integration for ERP-BERHAN."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from erp.extensions import db, login_manager
from erp.models.client_auth import ClientAccount


class User(UserMixin, db.Model):
    """Application user used for authentication."""

    __tablename__ = "users"

    # NOTE: This schema is aligned with your current DB table:
    # id | username | email | password_hash | created_at | updated_at
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
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


# ----------------------------------------------------------------------
# Flask-Login user loader – THIS FIXES THE 'Missing user_loader' ERROR
# ----------------------------------------------------------------------

@login_manager.user_loader
def load_user(user_id: str) -> Optional[User | ClientAccount]:
    """Load a user or client account from the session-stored identifier."""

    if not user_id:
        return None

    # Distinguish client principals to avoid ID collisions with employees
    if isinstance(user_id, str) and user_id.startswith("client:"):
        try:
            client_id = int(user_id.split(":", 1)[1])
        except (IndexError, ValueError):
            return None
        return ClientAccount.query.get(client_id)

    try:
        return User.query.get(int(user_id))
    except Exception:
        # Defensive: never crash request handling due to bad session data
        return None
