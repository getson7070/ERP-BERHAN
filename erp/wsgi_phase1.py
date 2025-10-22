from __future__ import annotations
import os
from flask import Flask

def _ensure_min_env() -> None:
    os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    os.environ.setdefault("SECRET_KEY", "dev-not-secret")

def build_app() -> Flask:
    _ensure_min_env()
    from erp.api.integrations import create_app  # type: ignore
    app: Flask = create_app()
    try:
        from erp.bootstrap_phase1 import apply_phase1_hardening  # type: ignore
        apply_phase1_hardening(app)
    except Exception as e:  # pragma: no cover
        app.logger.warning("Phase1 bootstrap skipped: %s", e)
    return app

app = build_app()
