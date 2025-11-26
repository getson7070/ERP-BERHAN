"""DEV/PHASE1 ONLY – NOT FOR PRODUCTION WSGI.

This minimal integrations stub supports early smoke testing. Production should
use the full app factory (``erp.app:app``) rather than this lightweight
blueprint set.
"""
from __future__ import annotations

from typing import Tuple
from flask import Flask, Blueprint, jsonify

# Endpoints we don't serve (kept for compatibility with erp.api.__init__ imports)
GRAPHQL_REJECTS: Tuple[str, ...] = ("/graphql", "/graphiql")

# Minimal integrations blueprint
integrations_bp = Blueprint("integrations", __name__)

@integrations_bp.get("/ping")
def ping() -> tuple[dict, int]:
    return {"status": "ok"}, 200

def create_app() -> Flask:
    """
    Minimal app factory expected by erp.api.__init__.
    Phase1 hardening is applied by erp.wsgi_phase1 (not here) to keep imports side-effect free.
    """
    app = Flask("erp")
    # Register blueprints
    app.register_blueprint(integrations_bp, url_prefix="/integrations")
    return app


