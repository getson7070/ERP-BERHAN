import importlib, pkgutil, inspect, os
from flask import Blueprint

SKIP_DIRS = {"tests", "migrations", "alembic", "venv", "env", "scripts", "tools", "docker"}
SKIP_SEGMENTS = tuple("." + s for s in SKIP_DIRS)

def find_roots(base="/app"):
    roots = []
    try:
        for name in os.listdir(base):
            p = os.path.join(base, name)
            if not os.path.isdir(p):
                continue
            if name.startswith(".") or name in SKIP_DIRS:
                continue
            if os.path.exists(os.path.join(p, "__init__.py")):
                roots.append(name)
    except Exception:
        pass
    # Always try "erp" if present in sys.path even if not under /app
    if "erp" not in roots:
        try:
            importlib.import_module("erp")
            roots.append("erp")
        except Exception:
            pass
    return sorted(set(roots))

def _iter_modules(pkg_name: str):
    try:
        pkg = importlib.import_module(pkg_name)
    except Exception:
        return
    if not hasattr(pkg, "__path__"):
        return
    for _, name, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        if any(seg in name for seg in SKIP_SEGMENTS):
            continue
        yield name

def discover_blueprints(pkgs=None):
    pkgs = pkgs or find_roots()
    for pkg_name in pkgs:
        for name in _iter_modules(pkg_name):
            try:
                m = importlib.import_module(name)
            except Exception:
                continue
            # yield ANY attribute that is a Blueprint instance
            for _, obj in inspect.getmembers(m, lambda o: isinstance(o, Blueprint)):
                yield obj, name

def register_all(app, pkgs=None):
    seen = set()
    found = []
    for bp, modname in discover_blueprints(pkgs):
        if bp.name in seen:
            continue
        app.register_blueprint(bp)  # url_prefix should be set where bp is defined
        seen.add(bp.name)
        found.append((bp.name, bp.url_prefix, modname))
    return found
