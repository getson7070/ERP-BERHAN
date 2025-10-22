
import os
from flask import request

# Transitional CSP to avoid breaking inline usages.
# Improve to nonce-based CSP in later phases.
DEFAULT_CSP = " ".join([
    "default-src 'self';",
    "img-src 'self' data:;",           # allow data: for small inline logos
    "style-src 'self' 'unsafe-inline';",
    "script-src 'self' 'unsafe-inline';",
    "connect-src 'self';",
    "frame-ancestors 'none';",
])

def add_security_headers(response):
    # Basic hardening
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

    # HSTS only when HTTPS
    try:
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
    except Exception:
        pass

    # Configurable CSP (transitional)
    csp = os.getenv("CSP", DEFAULT_CSP)
    if csp:
        response.headers.setdefault("Content-Security-Policy", csp)

    return response
