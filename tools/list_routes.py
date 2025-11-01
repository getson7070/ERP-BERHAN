import os, importlib, sys
from typing import Optional
from flask.cli import ScriptInfo
from flask import Flask

def _load_via_flask_cli() -> Optional[Flask]:
    # Use whatever FLASK_APP is set to (entrypoint sets a default)
    try:
        info = ScriptInfo(create_app=None)
        return info.load_app()
    except Exception:
        return None

def _try_candidates() -> Optional[Flask]:
    # Try common module:factory pairs
    candidates = [
        ("erp.boot", "create_app"),
        ("erp", "create_app"),
        ("app", "create_app"),
        ("server", "create_app"),
        ("application", "create_app"),
    ]
    for mod, obj in candidates:
        try:
            m = importlib.import_module(mod)
            f = getattr(m, obj, None)
            if callable(f):
                return f()
            # fallbacks: module exports 'app' or 'application'
            app = getattr(m, "app", None) or getattr(m, "application", None)
            if isinstance(app, Flask):
                return app
        except Exception:
            continue
    return None

# Preferred: FLASK_APP resolution
app = _load_via_flask_cli()
if app is None:
    # If FLASK_APP wasn't set in this exec, give it a sensible default and try again
    if "FLASK_APP" not in os.environ:
        os.environ["FLASK_APP"] = "erp.boot:create_app"
        app = _load_via_flask_cli()

# Fallback scanning
if app is None:
    app = _try_candidates()

if app is None:
    raise RuntimeError("Could not resolve the Flask app. Ensure FLASK_APP is set or erp.boot exists.")

print("=== Registered Blueprints ===")
for name, bp in sorted(app.blueprints.items()):
    print(f"{name} -> url_prefix={bp.url_prefix!r}")

print("=== URL Map ===")
for r in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = ",".join(sorted(m for m in r.methods if m not in {"HEAD","OPTIONS"}))
    print(f"{methods:10s} {r.rule:40s} -> {r.endpoint}")
