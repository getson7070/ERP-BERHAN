﻿from __future__ import annotations

import os
import uuid
from flask import Flask, g, request

def _truthy(v: str | None) -> bool:
    return v is not None and v.strip().lower() in {"1", "true", "yes", "on"}

def apply_phase1_hardening(app: Flask) -> None:
    """
    Phase-1: security headers, request-id, optional rate limiting, health bp.
    Idempotent and import-safe.
    """
    # --- Security headers ---
    csp = os.environ.get(
        "CSP",
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none';",
    )

    @app.before_request
    def _ensure_request_id() -> None:
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = rid

    @app.after_request
    def _security_headers(resp):
        resp.headers.setdefault("Content-Security-Policy", csp)
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        rid = getattr(g, "request_id", None)
        if rid:
            resp.headers["X-Request-ID"] = rid
        return resp

    # --- Optional rate limiting ---
    if _truthy(os.environ.get("PHASE1_ENABLE_LIMITER")):
        try:
            from erp.ext.limiter import install_limiter  # type: ignore
            install_limiter(app)
        except Exception as e:
            app.logger.warning("Phase1: limiter unavailable: %s", e)

    # --- Health blueprint (accept both `health_bp` and legacy `bp`) ---
    try:
        try:
            from erp.ops.health import health_bp as _bp  # type: ignore
        except ImportError:
            from erp.ops.health import bp as _bp  # type: ignore
        if _bp.name not in app.blueprints:
            app.register_blueprint(_bp)
    except Exception as e:
        app.logger.warning("Phase1: health blueprint not registered: %s", e)
