"""CSRF token helper endpoints for SPA/front-end clients."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify
from flask_wtf.csrf import generate_csrf

bp = Blueprint("csrf_api", __name__, url_prefix="/api/auth")


@bp.get("/csrf")
def get_csrf():
    """Return a CSRF token to be echoed in X-CSRF-Token on mutating requests."""

    return jsonify({"csrf_token": generate_csrf()}), HTTPStatus.OK


@bp.post("/csrf-check")
def csrf_check():
    """Lightweight endpoint used by automated checks to validate CSRF handling."""

    return jsonify({"status": "ok"}), HTTPStatus.OK


__all__ = ["bp"]
