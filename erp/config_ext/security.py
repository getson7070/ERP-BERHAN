from flask import Flask

def apply_security_defaults(app: Flask) -> None:
    # Secure cookie settings
    app.config.setdefault("SESSION_COOKIE_SECURE", True)
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Strict")
    # If using Flask-Session or custom sessions, ensure they respect these flags.

def register_secure_headers(app: Flask) -> None:
    @app.after_request
    def _secure_headers(resp):
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # Keep CSP minimal unless you audit front-end assets; too strict can break current UI.
        # resp.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        return resp
