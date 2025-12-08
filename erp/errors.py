"""Error handler registration with JSON/HTML aware responses."""

from __future__ import annotations

from flask import g, jsonify, render_template, request


def _wants_json() -> bool:
    """Detect whether the requester expects JSON instead of HTML."""

    accept = request.accept_mimetypes
    wants_json = request.is_json or request.path.startswith("/api")
    return wants_json or (accept.best == "application/json" and accept.best != "text/html")


def _payload(msg: str, status: int):
    """Return a JSON-friendly payload with request correlation."""

    rid = getattr(g, "request_id", None)
    return jsonify(error=msg, request_id=rid, status=status), status


def _render_or_payload(status: int, title: str, description: str, cta_href: str | None = None):
    """Render an HTML error page when the client accepts HTML, otherwise JSON."""

    if _wants_json():
        return _payload(title.lower().replace(" ", "_"), status)

    context = {
        "status": status,
        "title": title,
        "description": description,
        "cta_href": cta_href,
        "request_id": getattr(g, "request_id", None),
    }
    template_name = f"errors/{status}.html"
    return render_template(template_name, **context), status


def register_error_handlers(app):
    """Register JSON + HTML aware error handlers for key HTTP statuses."""

    @app.errorhandler(400)
    def bad_request(e):  # pragma: no cover
        return _render_or_payload(400, "Bad request", "Please verify the request and try again." )

    @app.errorhandler(401)
    def unauthorized(e):  # pragma: no cover
        return _render_or_payload(401, "Authentication required", "Sign in to continue.", cta_href="/login")

    @app.errorhandler(403)
    def forbidden(e):  # pragma: no cover
        return _render_or_payload(403, "Access denied", "You do not have permission to view this page.")

    @app.errorhandler(404)
    def not_found(e):  # pragma: no cover
        return _render_or_payload(404, "Page not found", "The page you are looking for does not exist or has moved.", cta_href="/")

    @app.errorhandler(Exception)
    def server_error(e):  # pragma: no cover
        app.logger.exception("uncaught_exception")
        return _render_or_payload(500, "Something went wrong", "We hit an unexpected error. Please try again or contact support.")

    return app



