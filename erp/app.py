import os
import importlib
import pkgutil
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader
from flask import Blueprint

from .extensions import socketio, db, migrate, limiter
from .config import Settings
from .capabilities import choose_async_mode, maybe_init_sentry
from .web import web_bp


def _iter_blueprints(package_module):
    prefix = package_module.__name__ + "."
    for _, modname, _ in pkgutil.walk_packages(package_module.__path__, prefix):
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:
            print(f"[blueprints] skip {modname}: {exc}")
            continue
        for obj in mod.__dict__.values():
            if isinstance(obj, Blueprint):
                yield obj, modname


def _register_all_blueprints(app: Flask):
    seen = set()
    for pkgname in ("erp.routes", "erp.blueprints", "plugins"):
        try:
            pkg = importlib.import_module(pkgname)
        except ModuleNotFoundError:
            continue

        for bp, modname in _iter_blueprints(pkg):
            name = bp.name
            if name in seen or name in app.blueprints:
                new_name = f"{name}__{modname.split('.')[-1]}"
                try:
                    bp.name = new_name
                    print(f"[blueprints] renamed duplicate '{name}' -> '{new_name}' from {modname}")
                except Exception as exc:
                    print(f"[blueprints] could not rename '{name}' from {modname}: {exc}; skipping")
                    continue
            try:
                app.register_blueprint(bp)
                seen.add(bp.name)
            except Exception as exc:
                print(f"[blueprints] failed to register {bp.name} from {modname}: {exc}")


def create_app() -> Flask:
    s = Settings()

    pkg_root = Path(__file__).resolve().parent          # .../erp
    repo_root = pkg_root.parent                         # repo root

    app = Flask(__name__)
        @app.context_processor
    def _inject_globals():
        # Provide a no-op translation function if Flask-Babel isn't wired.
        return {"_": (lambda s, **kwargs: s)}
    app.config["JSON_SORT_KEYS"] = False
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-me-now")
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    # ---- Jinja: assemble a resilient loader chain
    root_templates = repo_root / "templates"
    erp_templates = pkg_root / "templates"

    chain = []
    if root_templates.is_dir():
        chain.append(FileSystemLoader(str(root_templates)))
    if erp_templates.is_dir():
        chain.append(FileSystemLoader(str(erp_templates)))
    # Keep Flask's default loader (erp/templates relative to app.root_path)
    if app.jinja_loader:
        chain.append(app.jinja_loader)

    if chain:
        app.jinja_loader = ChoiceLoader(chain)

    # Startup diagnostics: log whether the expected entry templates exist
    for cand in ("auth/login.html", "choose_login.html", "login.html", "index.html"):
        exists_root = (root_templates / cand).exists() if root_templates.is_dir() else False
        exists_erp  = (erp_templates / cand).exists() if erp_templates.is_dir() else False
        app.logger.warning(f"[templates] check {cand}: root={exists_root} erp={exists_erp}")

    # ---- Static: root /static and optional /erp-static
    root_static = repo_root / "static"
    if root_static.is_dir():
        app.static_folder = str(root_static)
        app.static_url_path = "/static"
    erp_static = pkg_root / "static"
    if erp_static.is_dir():
        @app.route("/erp-static/<path:filename>")
        def _erp_static(filename):
            return send_from_directory(str(erp_static), filename)

    # ---- DB
    if s.DATABASE_URL:
        app.config["SQLALCHEMY_DATABASE_URI"] = s.DATABASE_URL
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)
        migrate.init_app(app, db)

    # ---- Limiter (imported by auth routes)
    limiter.init_app(app)

    # ---- Observability
    maybe_init_sentry(s)

    # ---- Socket.IO
    async_mode = choose_async_mode(s)
    socketio.init_app(
        app,
        async_mode=async_mode,
        cors_allowed_origins="*",
        message_queue=s.SOCKETIO_MESSAGE_QUEUE or None,
    )
    try:
        app.logger.info(f"Flask-SocketIO async_mode: {async_mode}")
    except Exception:
        pass

    # ---- Probes
    @app.get("/health")
    def health():
        return jsonify({"app": "ERP-BERHAN", "status": "running"})

    @app.get("/ready")
    def ready():
        return jsonify({
            "socketio": async_mode,
            "db": bool(s.DATABASE_URL),
            "observability": bool(s.SENTRY_DSN) and s.ENABLE_OBSERVABILITY,
            "auto_migrate": bool(s.MIGRATE_ON_STARTUP),
        })

    # ---- Register blueprints (robust)
    _register_all_blueprints(app)

    # ---- Fallback UI (only used if app didn't supply /)
    app.register_blueprint(web_bp)

    # ---- Optional startup migrations
    if s.MIGRATE_ON_STARTUP and s.DATABASE_URL:
        _safe_upgrade_head(app)

    return app


def _safe_upgrade_head(app: Flask):
    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command as alembic_command
        cfg = AlembicConfig(os.getenv("ALEMBIC_INI", "alembic.ini"))
        alembic_command.upgrade(cfg, "head")
        app.logger.info("Startup migration: upgrade to head completed.")
    except Exception as exc:
        app.logger.warning(f"Startup migration skipped or failed: {exc}")
