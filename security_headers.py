from typing import Optional
def init_app(app, *, csp: Optional[str] = None):
    app.config.setdefault("STRICT_TRANSPORT_SECURITY", "max-age=63072000; includeSubDomains; preload")
    app.config.setdefault("CONTENT_SECURITY_POLICY", csp or "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'")
    app.config.setdefault("X_FRAME_OPTIONS", "DENY")
    app.config.setdefault("X_CONTENT_TYPE_OPTIONS", "nosniff")
    app.config.setdefault("REFERRER_POLICY", "strict-origin-when-cross-origin")
    @app.after_request
    def _secure(resp):
        resp.headers["Strict-Transport-Security"] = app.config["STRICT_TRANSPORT_SECURITY"]
        resp.headers["Content-Security-Policy"] = app.config["CONTENT_SECURITY_POLICY"]
        resp.headers["X-Frame-Options"] = app.config["X_FRAME_OPTIONS"]
        resp.headers["X-Content-Type-Options"] = app.config["X_CONTENT_TYPE_OPTIONS"]
        resp.headers["Referrer-Policy"] = app.config["REFERRER_POLICY"]
        return resp
