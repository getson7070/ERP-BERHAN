
import logging

def apply_phase1_hardening(app):
    """Attach Phase 1 hardening to a Flask app in a safe, idempotent way."""
    # Idempotency guard
    if getattr(app, "_phase1_hardened", False):
        return app

    # Lazy imports to avoid breaking if optional deps missing
    from .middleware.request_id import ensure_request_id, add_request_id_to_response
    from .middleware.security_headers import add_security_headers

    # Request ID (before) and add to response (after)
    app.before_request(ensure_request_id)
    app.after_request(add_request_id_to_response)

    # Security headers (after request)
    app.after_request(add_security_headers)

    # Health endpoints
    try:
        from .ops.health import bp as health_bp
        app.register_blueprint(health_bp, url_prefix="/")
    except Exception as e:  # pragma: no cover
        app.logger.warning("Phase1: health blueprint not registered: %s", e)

    # Optional rate limiting
    try:
        from .ext.limiter import limiter, configure_rate_limits
        configure_rate_limits(app)
        limiter.init_app(app)
    except Exception as e:  # pragma: no cover
        app.logger.warning("Phase1: Limiter not active: %s", e)

    app._phase1_hardened = True
    app.logger.info("Phase1 hardening applied.")
    return app
