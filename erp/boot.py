from typing import Optional, Callable
from flask import Flask

def _try_factories():
    # Env-configurable first
    import os, import importlib
    env = os.getenv("APP_FACTORY")
    if env:
        mod, _, obj = env.partition(":")
        try:
            m = importlib.import_module(mod)
            f = getattr(m, obj, None)
            if callable(f):
                yield f, f"{mod}:{obj}"
        except Exception:
            pass
    # Typical candidates
    candidates = [
        ("erp", "create_app"),
        ("app", "create_app"),
        ("server", "create_app"),
        ("application", "create_app"),
        ("wsgi", "create_app"),
        ("main", "create_app"),
        ("backend", "create_app"),
    ]
    import importlib
    for mod, obj in candidates:
        try:
            m = importlib.import_module(mod)
            f = getattr(m, obj, None)
            if callable(f):
                yield f, f"{mod}:{obj}"
        except Exception:
            continue

def _try_instances():
    # If someone exposes app/application directly
    candidates = ["erp","app","server","application","wsgi","main","backend"]
    import importlib
    for mod in candidates:
        try:
            m = importlib.import_module(mod)
            a = getattr(m, "app", None) or getattr(m, "application", None)
            if isinstance(a, Flask):
                yield a, f"{mod}:app"
        except Exception:
            continue

def _resolve_base_app() -> Flask:
    last_err = None
    for f, where in _try_factories():
        try:
            app = f()
            try:
                app.logger.info("Base app factory resolved from %s", where)
            except Exception:
                print("Base app factory resolved from", where)
            return app
        except Exception as e:
            last_err = e
            continue
    for a, where in _try_instances():
        try:
            a.logger.info("Base app instance resolved from %s", where)
        except Exception:
            print("Base app instance resolved from", where)
        return a
    # Fallback minimal app (keeps health working, but signals warning)
    from flask import Flask
    app = Flask(__name__)
    @app.get("/health")
    def _h(): return "ok", 200
    try:
        app.logger.warning("FALLBACK app created; no known factory/instance was found. Set APP_FACTORY or add create_app().")
    except Exception:
        print("FALLBACK app created; no known factory/instance was found. Set APP_FACTORY or add create_app().")
    return app

def create_app(*args, **kwargs):
    app = _resolve_base_app()
    # Register all discovered blueprints from first-party roots
    try:
        from .auto_blueprints import register_all, find_roots
        registered = register_all(app, pkgs=find_roots("/app"))
        msg = ("Auto-registered blueprints: " + ", ".join(f"{n}@{m} prefix={p!r}" for n,p,m in registered)) if registered else "No blueprints discovered"
        try:
            app.logger.info(msg)
        except Exception:
            print(msg)
    except Exception as e:
        try:
            app.logger.warning(f"Auto blueprint registration skipped: {e}")
        except Exception:
            print("Auto blueprint registration skipped:", e)
    return app
