# erp/__init__.py
from __future__ import annotations

import os
from datetime import datetime
from typing import Dict

from flask import Flask, render_template, request
from .security import read_device_id, compute_activation_for_device

# Import shared extensions (instances only; no heavy app logic here)
# Your erp/extensions.py must define these objects.
from .extensions import (
    db,
    migrate,
    csrf,
    login_manager,
    limiter,
    cache,
    mail,
    socketio,
)
try:
    # CORS is optional; only init if present to avoid ImportError mismatches.
    from .extensions import cors  # type: ignore
except Exception:  # pragma: no cover
    cors = None  # type: ignore


def create_app() -> Flask:
    """Application factory used by wsgi and tests."""
    app = Flask(__name__, instance_relative_config=False)

    # ---- Base configuration (Render env already provides these) ----
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    # ---- Init extensions ----
    db.init_app(app)
    migrate.
