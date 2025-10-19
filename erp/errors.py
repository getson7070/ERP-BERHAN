
from __future__ import annotations
from flask import jsonify, g

def register_error_handlers(app):
    def _payload(msg, status):
        rid = getattr(g, "request_id", None)
        return jsonify(error=msg, request_id=rid, status=status), status

    @app.errorhandler(400)
    def bad_request(e):  # pragma: no cover
        return _payload("bad_request", 400)

    @app.errorhandler(401)
    def unauthorized(e):  # pragma: no cover
        return _payload("unauthorized", 401)

    @app.errorhandler(403)
    def forbidden(e):  # pragma: no cover
        return _payload("forbidden", 403)

    @app.errorhandler(404)
    def not_found(e):  # pragma: no cover
        return _payload("not_found", 404)

    @app.errorhandler(Exception)
    def server_error(e):  # pragma: no cover
        app.logger.exception("uncaught_exception")
        return _payload("internal_error", 500)

    return app


