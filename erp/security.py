from __future__ import annotations
from typing import Optional
import os

def apply_security(app) -> None:
    """Harden cookies, enable CSP/HSTS if Flask-Talisman is available."""
    # Core cookies
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("REMEMBER_COOKIE_SECURE", True)
    app.config.setdefault("REMEMBER_COOKIE_HTTPONLY", True)

    # Basic CSP/HSTS via Talisman if installed
    try:
        from talisman import Talisman  # pip: flask-talisman or talisman (alias)
    except Exception:
        try:
            from flask_talisman import Talisman  # legacy pkg name
        except Exception:
            Talisman = None

    if Talisman:
        csp = {
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:"],
            "font-src": ["'self'", "data:"],
            "connect-src": ["'self'"],
            "object-src": ["'none'"],
            "frame-ancestors": ["'self'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
        }
        Talisman(
            app,
            content_security_policy=csp,
            force_https=False,  # behind proxies this should be True with proper proxy headers
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
        )
