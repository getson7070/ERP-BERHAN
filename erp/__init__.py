"""ERP-BERHAN application factory and blueprint registration helpers."""
from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Iterable

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from db import redis_client  # type: ignore

from .db import db as db
from .dlq import _dead_letter_handler
from .extensions import cache, init_extensions, limiter, login_manager, mail
from .metrics import (
    AUDIT_CHAIN_BROKEN,
    DLQ_MESSAGES,
    GRAPHQL_REJECTS,
    QUEUE_LAG,
    RATE_LIMIT_REJECTIONS,
)
from .socket import socketio
from .security import apply_security

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _load_config(app: Flask) -> None:
    """Populate ``app.config`` from the canonical Config object or env vars."""

    try:
        from config import Config  # type: ignore
    except ImportError:  # pragma: no cover - fallback only hit in minimal envs
        Config = None  # type: ignore

    if Config is not None:
        app.config.from_object(Config)
        return

    # Fallback configuration mirrors the documented deployment defaults.
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        database_path = os.environ.get("DATABASE_PATH")
        if database_path:
            database_url = f"sqlite:///{database_path}"
        else:
            database_url = "sqlite:///local.db"

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "change-me"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=True,
        REMEMBER_COOKIE_HTTPONLY=True,
        WTF_CSRF_TIME_LIMIT=None,
    )


# ---------------------------------------------------------------------------
# Blueprint discovery
# ---------------------------------------------------------------------------

_MANIFEST = Path(__file__).resolve().parent.parent / "blueprints_dedup_manifest.txt"
_DEFAULT_BLUEPRINT_MODULES = [
    "erp.main",
    "erp.web",
    "erp.views_ui",
    "erp.routes.main",
    "erp.routes.dashboard_customize",
    "erp.routes.analytics",
    "erp.blueprints.inventory",
]

_EXCLUDED_BLUEPRINT_MODULES = {
    "erp.health_checks",
    "erp.blueprints.health_compat",
    "erp.ops.health",
    "erp.ops.status",
}


def _iter_blueprint_modules() -> Iterable[str]:
    """Yield dotted module paths that are expected to expose a Blueprint."""

    seen: set[str] = set()

    if _MANIFEST.exists():
        for line in _MANIFEST.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            if line.startswith("CHOSEN") or line.startswith("SKIPPED"):
                continue
            if line.startswith("- "):
                try:
                    _, remainder = line.split(":", 1)
                except ValueError:
                    continue
                module = remainder.strip().split()[0]
                if "." in module:
                    module = module.rsplit(".", 1)[0]
                if module:
                    seen.add(module)
                    yield module
        for module in _DEFAULT_BLUEPRINT_MODULES:
            if module not in seen:
                yield module
        return

    # Fallback: curated allow-list for minimal environments/tests.
    try:
        from .blueprints_explicit import ALLOWLIST
    except Exception:  # pragma: no cover - defensive fallback
        ALLOWLIST = []  # type: ignore

    seen.update(_DEFAULT_BLUEPRINT_MODULES)

    allowlist_modules = [module for module, _ in ALLOWLIST]
    for module in allowlist_modules:
        yield module

    for module in _DEFAULT_BLUEPRINT_MODULES:
        if module not in allowlist_modules:
            yield module


def _resolve_blueprint(module) -> "Blueprint":
    from flask import Blueprint

    candidate_attrs = ("bp", "blueprint", "app")
    for attr in candidate_attrs:
        obj = getattr(module, attr, None)
        if isinstance(obj, Blueprint):
            return obj

    for obj in module.__dict__.values():
        if isinstance(obj, Blueprint):
            return obj

    raise RuntimeError(f"No Flask Blueprint found in module {module.__name__!r}")


def register_blueprints(app: Flask) -> None:
    """Import and register each blueprint exactly once."""

    seen: dict[tuple[str, str], str] = {}

    for dotted_path in _iter_blueprint_modules():
        if dotted_path in _EXCLUDED_BLUEPRINT_MODULES:
            LOGGER.debug("Skipping blueprint module %s via exclusion list", dotted_path)
            continue
        try:
            module = importlib.import_module(dotted_path)
        except Exception as exc:  # pragma: no cover - log and continue
            LOGGER.warning("Skipping blueprint module %s: %s", dotted_path, exc)
            continue

        try:
            blueprint = _resolve_blueprint(module)
        except Exception as exc:  # pragma: no cover - log and continue
            LOGGER.warning("Module %s does not expose a blueprint: %s", dotted_path, exc)
            continue

        if blueprint.name in app.blueprints:
            LOGGER.info(
                "Skipping blueprint %s from %s because name already registered",
                blueprint.name,
                dotted_path,
            )
            continue

        key = (blueprint.name, blueprint.url_prefix or "")
        if key in seen:
            LOGGER.info(
                "Duplicate blueprint name/prefix detected (name=%s, prefix=%s) from %s;"
                " keeping first definition from %s",
                blueprint.name,
                blueprint.url_prefix or "",
                dotted_path,
                seen[key],
            )
            continue

        app.register_blueprint(blueprint)
        seen[key] = dotted_path
        LOGGER.debug(
            "Registered blueprint %s from %s (prefix=%s)",
            blueprint.name,
            dotted_path,
            blueprint.url_prefix,
        )


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def _register_core_routes(app: Flask) -> None:
    routes = {rule.rule for rule in app.url_map.iter_rules()}

    if "/healthz" not in routes:

        @app.get("/healthz")
        def healthz():
            return jsonify(status="ok"), 200


def create_app(config_object: str | None = None) -> Flask:
    """Application factory used by Flask, Celery, and CLI tooling."""

    app = Flask(__name__, instance_relative_config=False)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    if config_object:
        app.config.from_object(config_object)
    else:
        _load_config(app)

    init_extensions(app)
    apply_security(app)
    register_blueprints(app)
    _register_core_routes(app)

    # Ensure models are imported for Alembic autogenerate & shell usage.
    try:  # pragma: no cover - imports for side effects only
        importlib.import_module("erp.models")
    except Exception as exc:
        LOGGER.debug("Model import failed during boot: %s", exc)

    return app


__all__ = [
    "create_app",
    "register_blueprints",
    "db",
    "cache",
    "mail",
    "limiter",
    "login_manager",
    "redis_client",
    "socketio",
    "QUEUE_LAG",
    "RATE_LIMIT_REJECTIONS",
    "GRAPHQL_REJECTS",
    "AUDIT_CHAIN_BROKEN",
    "DLQ_MESSAGES",
    "_dead_letter_handler",
]
