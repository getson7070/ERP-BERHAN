"""User model and Flask-Login integration for ERP-BERHAN.

This model is intentionally conservative:

- Keeps the existing INTEGER primary key `id` to avoid breaking foreign keys
  or the current Alembic chain.
- Adds a *secondary* UUID column `uuid` that can be used as a stable,
  non-guessable public identifier in APIs, URLs, and integrations.
- Preserves the existing unique constraints and relationships.
- Adds role-based helper properties for:
    - role_names
    - has_role / has_any_role
    - is_management
    - is_supervisor
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable, List, Set
from uuid import uuid4

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from erp.extensions import db

try:
    # This is safe to import even if you run on SQLite; SQLAlchemy will
    # fall back to an appropriate generic type when not on Postgres.
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
except Exception:  # pragma: no cover - extremely defensive fallback
    PG_UUID = db.String  # type: ignore[assignment]

from erp.models.role import Role  # UPGRADE: Import for RBAC

class User(UserMixin, db.Model):
    """Application user used for authentication."""

    __tablename__ = "users"
    __table_args__ = (
        db.UniqueConstraint("org_id", "telegram_chat_id", name="uq_users_org_chat"),
    )

    # NOTE: This schema is aligned with your current DB table:
    # id | org_id | username | email | password_hash | created_at | updated_at | ...
    # We ADD a UUID column but do not remove or rename anything.

    id = db.Column(db.Integer, primary_key=True)

    # New: secondary UUID identifier for safer public exposure (preserve original UUID logic)
    uuid = db.Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        unique=True,
        default=uuid4,
        index=True,
    )

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

    # Many-to-many via `user_role_assignments` (already exists in your DB) - UPGRADE: Use user_roles
    roles = db.relationship(
        "Role",
        secondary="user_roles",  # UPGRADE: Point to new user_role table
        backref="users",
        lazy="select",
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
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
        """
        Flask-Login stores IDs as strings in the session.

        IMPORTANT:
        - We KEEP returning `id` (integer) here for backwards compatibility.
        - For external/public identifiers, prefer `self.uuid` or `self.public_id`.
        """
        return str(self.id)

    # ------------------------------------------------------------------
    # UUID / public identifier helpers (preserve)
    # ------------------------------------------------------------------
    @property
    def public_id(self) -> str:
        """
        Stable, non-guessable identifier suitable for URLs, APIs, bots, etc.

        Example usage:
            /api/users/<public_id>
        """
        return str(self.uuid)

    # ------------------------------------------------------------------
    # Role / RBAC helper properties (preserve + UPGRADE: Add has_permission dynamic)
    # ------------------------------------------------------------------
    @property
    def role_names(self) -> List[str]:
        """Return a sorted list of role names assigned to this user."""
        names: Set[str] = set()
        for role in self.roles or []:
            name = (getattr(role, "name", "") or "").strip().lower()
            if name:
                names.add(name)
        return sorted(names)

    def has_role(self, name: str) -> bool:
        """
        Check if the user has a specific role name (case-insensitive).
        """
        target = name.strip().lower()
        return target in self.role_names

    def has_any_role(self, *names: Iterable[str]) -> bool:
        """
        Check if the user has ANY of the given role names or prefixes.

        This is intentionally flexible so you can do things like:
            user.has_any_role("admin", "technical_manager", "finance_manager")
        """
        if not names:
            return False

        role_names = self.role_names
        if not role_names:
            return False

        # Flatten and normalise
        candidates: List[str] = []
        for n in names:
            if isinstance(n, str):
                candidates.append(n.strip().lower())
            else:
                for inner in n:  # supports has_any_role(["a", "b"])
                    candidates.append(str(inner).strip().lower())

        for candidate in candidates:
            if not candidate:
                continue
            # Exact match
            if candidate in role_names:
                return True
            # Prefix match (for e.g. "technical_manager" vs "manager")
            for rn in role_names:
                if rn.startswith(candidate) or candidate.startswith(rn):
                    return True
        return False

    # UPGRADE: Dynamic has_permission (integrates with new Permission model)
    def has_permission(self, perm_name: str) -> bool:
        """Check if any role grants the permission (admin wildcard)."""
        if self.has_any_role("admin", "management"):
            return True
        for role in self.roles or []:
            # UPGRADE: Query role_permissions via relationship
            if any(p.name.lower() == perm_name.lower() for p in role.permissions or []):
                return True
        return False

    def has_any_permission(self, *perm_names: str) -> bool:
        """Check any of given permissions."""
        return any(self.has_permission(p) for p in perm_names)

    @property
    def is_management(self) -> bool:
        """
        Management-level staff – can see analytics and approve at higher level.

        This is based on ROLE NAMES, not the Employee.role text.

        By convention, you can map:
          - "admin"
          - "technical_manager"
          - "finance_manager"
          - "warehouse_manager"
          - "hr_manager"
          - "marketing_manager"
          - "general_manager"
          - "operations_manager"
        etc. via the RBAC seeding / assignments.
        """
        management_role_keys = {
            "admin",
            "technical_manager",
            "finance_manager",
            "warehouse_manager",
            "hr_manager",
            "marketing_manager",
            "general_manager",
            "operations_manager",
            "ceo",
            "cto",
            "cfo",
        }

        rn = set(self.role_names)
        if not rn:
            return False

        # Direct matches
        if rn & management_role_keys:
            return True

        # Fallback: any role containing "manager" or "director"
        for name in rn:
            if "manager" in name or "director" in name:
                return True

        return False

    @property
    def is_supervisor(self) -> bool:
        """
        Supervisor-level staff – can see reports and manage team work, but
        don't get full analytics like management.

        Example roles:
          - "sales_supervisor"
          - "senior_accountant"
          - "senior_purchaser"
          - "service_supervisor"
          - "team_lead_*"
        """
        # If you're already management, treat that as higher level
        if self.is_management:
            return False

        supervisor_keys = {
            "sales_supervisor",
            "senior_accountant",
            "senior_purchaser",
            "service_supervisor",
            "team_lead",
        }

        rn = set(self.role_names)
        if not rn:
            return False

        if rn & supervisor_keys:
            return True

        for name in rn:
            if "supervisor" in name:
                return True
            if name.startswith("team_lead"):
                return True
            if name.startswith("senior_"):
                return True

        return False

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"<User id={self.id!r} uuid={self.uuid!s} "
            f"org_id={self.org_id!r} username={self.username!r}>"
        )