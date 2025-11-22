"""Simple security headers middleware.

This complements the optional Flask-Talisman integration by ensuring that
baseline headers are always applied even when Talisman is not installed.
"""

from __future__ import annotations

from flask import Flask


def apply_security_headers(app: Flask) -> None:
    """Attach a minimal after-request hook that sets common security headers."""

    @app.after_request
    def _add_headers(response):  # type: ignore[nested-function-redefinition]
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'self'; frame-ancestors 'none';"
        )
        return response


__all__ = ["apply_security_headers"]
