from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Iterable, List

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from erp.extensions import init_extensions  # your existing extensions init


def _load_config(app: Flask) -> None:
    """
    Load configuration for the Flask app.

    Priority:
      1) erp.config.Config if present
      2) Fallback Config class that requires env vars:
         - SECRET_KEY
         - DATABASE_URL
    """
    try:
        from erp.config import Config  # type: ignore
    except ImportError:
        class Config:  # type: ignore[no-redef]
            SECRET_KEY = os.environ["SECRET_KEY"]
            SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            WTF_CSRF_ENABLED = True

    app.config.from_object(Config)


# ---------- Blueprint discovery / registration ----------

def _iter_blueprint_modules() -> Iterable[str]:
    """
    Yield dotted *module* paths for blueprints listed in
    `blueprints_dedup_manifest.txt`.

    Your manifest currently looks like:

        - health_bp: erp.health_checks.health_bp (C:\\...\\health_checks.py)
        - web: erp.web.web_bp (C:\\...\\web.py)
        ...
        # SKIPPED (same name):
        - recall: erp.blueprints.recall.recall_bp (C:\\...\\__init__.py)
        ...

    From each line we want to extract the **module path**, e.g.:

        "erp.health_checks"
        "erp.web"
        "erp.routes.admin"
        ...

    We:
      * ignore comments and blank lines,
      * only consider lines starting with "- ",
      * take the text after the colon (":") -> e.g. "erp.routes.admin.bp (C:...)",
      * strip off the file path "(C:...)" part,
      * strip off the trailing ".bp" / ".health_bp" / ".main_bp" so we end up with
        just the module path.
    """
    root = Path(__file__).resolve().parent.parent  # project root
    manifest = root / "blueprints_dedup_manifest.txt"
    if not manifest.exists():
        return []

    modules: List[str] = []

    with manifest.open() as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                # comments and blank lines
                continue

            if not line.startswith("- "):
                # ignore anything not following "- name: module (path)" pattern
                continue

            # Strip "- " prefix
            line = line[2:].strip()

            # Expect "label: dotted.path.to.bp (C:\\...)" form
            if ":" not in line:
                continue

            _, rest = line.split(":", 1)
            rest = rest.strip()
            if not rest:
                continue

            # cut off "(C:\\...)" part if present
            if "(" in rest:
                rest = rest.split("(", 1)[0].strip()

            # rest should now look like "erp.routes.admin.bp"
            if not rest.startswith("erp."):
                continue

            dotted = rest.split()[0]  # in case there are stray spaces
            # turn "erp.routes.admin.bp" -> "erp.routes.admin"
            if "." in dotted:
                module_path = dotted.rsplit(".", 1)[0]
            else:
                module_path = dotted

            modules.append(module_path)

    # Deduplicate while preserving order
    seen_mods = set()
    ordered: List[str] = []
    for m in modules:
        if m not in seen_mods:
            seen_mods.add(m)
            ordered.append(m)

    return ordered


def _find_blueprint(module):
    """
    Return a Flask Blueprint object from a module.

    Preference:
      1. module.bp (common pattern)
      2. any attribute that is a Blueprint instance
         (so main_bp, health_bp, etc will be picked up).
    """
    from flask import Blueprint  # local import to avoid circular issues

    bp = getattr(module, "bp", None)
    if isinstance(bp, Blueprint):
        return bp

    for attr in module.__dict__.values():
        if isinstance(attr, Blueprint):
            return attr

    raise RuntimeError(f"No blueprint found in module {module.__name__!r}")


def register_blueprints(app: Flask) -> None:
    """
    Register all blueprints, skipping duplicates by (name, url_prefix).

    This prevents confusing errors when multiple modules reuse the same
    blueprint name or URL prefix. Duplicates are logged and skipped.
    """
    seen: dict[tuple[str, str], str] = {}

    for dotted_path in _iter_blueprint_modules():
        module = importlib.import_module(dotted_path)
        bp = _find_blueprint(module)

        name = bp.name
        prefix = bp.url_prefix or ""
        key = (name, prefix)

        if key in seen:
            app.logger.warning(
                "Skipping duplicate blueprint: name=%r prefix=%r from %s "
                "(already registered from %s)",
                name,
                prefix,
                dotted_path,
                seen[key],
            )
            continue

        app.register_blueprint(bp)
        seen[key] = dotted_path
        app.logger.info(
            "Registered blueprint %r (prefix=%r) from %s",
            bp.name,
            bp.url_prefix,
            dotted_path,
        )


# ---------- Core routes / utilities ----------

def _register_core_routes(app: Flask) -> None:
    """Register small core routes like /healthz."""

    @app.get("/healthz")
    def healthz():
        # Simple health check for Docker / LB probes
        return jsonify(status="ok")


# ---------- Application factory ----------

def create_app(config_object: str | None = None) -> Flask:
    """
    Flask application factory used by Gunicorn/Celery and `FLASK_APP=erp:create_app`.
    """
    app = Flask(__name__, instance_relative_config=False)

    # Ensure scheme/host are correct behind proxy/Render
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    if config_object:
        app.config.from_object(config_object)
    else:
        _load_config(app)

    # Initialise db, migrate, login_manager, mail, cache, limiter, etc.
    init_extensions(app)

    # Register blueprints from manifest (with duplicate protection)
    register_blueprints(app)

    # Core routes such as /healthz
    _register_core_routes(app)

    return app
