# erp/models.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
try:
    import pyotp
except ImportError:
    pyotp = None

from .extensions import db

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # "admin" | "employee" | "client"
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    mfa_secret = db.Column(db.String(32), nullable=True)


    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    def enable_mfa(self) -> None:
        """Enable multi-factor authentication for this user."""
        self.mfa_enabled = True
        # Generate a random 32-character secret for TOTP
        self.mfa_secret = secrets.token_hex(16)

    def verify_mfa(self, token: str) -> bool:
        """Verify a provided MFA token using TOTP. Returns False if MFA is disabled."""
        if not self.mfa_enabled or not self.mfa_secret:
            return False
        if pyotp:
            totp = pyotp.TOTP(self.mfa_secret)
            return bool(totp.verify(token))
        # Fallback: cannot verify without pyotp installed
        return False

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"




    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
