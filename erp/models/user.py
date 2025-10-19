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
# --- Write-only password shim for tests/dev ---
try:
    # Reuse the argon2 config you added in init_db.py
    from init_db import hash_password as _hash_password, verify_password as _verify_password
except Exception:
    def _hash_password(v: str) -> str: return v
    def _verify_password(pw: str, hashed: str) -> bool: return pw == hashed

def _user_get_password(self):
    # write-only; reading is intentionally disabled
    return None

def _user_set_password(self, raw):
    # If the model defines password_hash, store a hash there; else stash plain (tests only)
    try:
        if hasattr(self, "password_hash"):
            self.password_hash = _hash_password(raw)
        else:
            setattr(self, "_password", raw)
    except Exception:
        setattr(self, "_password", raw)

def _user_verify(self, raw):
    if getattr(self, "password_hash", None):
        try:
            return _verify_password(raw, self.password_hash)
        except Exception:
            return False
    return getattr(self, "_password", None) == raw

# Only add if not already present
if not hasattr(User, "password"):
    User.password = property(_user_get_password, _user_set_password)
if not hasattr(User, "verify_password"):
    User.verify_password = _user_verify
# --- /password shim ---
