import importlib, pkgutil, inspect, os, json, re
from typing import Iterable, Tuple

SKIP_DIRS = {"tests","migrations","alembic","docker","tools","scripts","_backup","backup","venv",".venv"}

def _iter_submodules(pkgname: str) -> Iterable[str]:
    m = importlib.import_module(pkgname)
    pkgpath = os.path.dirname(m.__file__)
    for finder, name, ispkg in pkgutil.walk_packages([pkgpath], prefix=pkgname+"."):
        parts = name.split(".")
        if any(p in SKIP_DIRS for p in parts):
            continue
        yield name

def register_all_unique(app, pkgs=("erp",)) -> Tuple[list, list]:
    """Import and register all Blueprint instances found under pkgs.
    Returns (registered, collisions) where each item is (import_path, bp_name, url_prefix).
    Collisions are resolved by appending '-2','-3' to prefix based on bp.name.
    """
    from flask import Blueprint
    registered = []
    collisions = []
    used_prefixes = set([bp.url_prefix or "" for bp in app.blueprints.values() if bp])
    for root in pkgs:
        for modname in _iter_submodules(root):
            try:
                mod = importlib.import_module(modname)
            except Exception:
                continue
            for name, obj in inspect.getmembers(mod):
                if isinstance(obj, Blueprint):
                    prefix = obj.url_prefix or f"/{obj.name}"
                    base = prefix
                    i = 2
                    while prefix in used_prefixes:
                        prefix = f"{base}-{i}"
                        i += 1
                    if prefix != (obj.url_prefix or ""):
                        collisions.append((modname, obj.name, prefix))
                    app.register_blueprint(obj, url_prefix=prefix)
                    used_prefixes.add(prefix)
                    registered.append((modname, obj.name, prefix))
    return registered, collisions

def write_discovery_snapshot(app, registered: list) -> None:
    try:
        os.makedirs("var", exist_ok=True)
        data = {"registered": registered, "count": len(registered)}
        with open("var/blueprints_discovered.json","w",encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        app.logger.info("Wrote blueprint discovery snapshot to var/blueprints_discovered.json")
    except Exception as e:
        app.logger.warning("Failed to write discovery snapshot: %s", e)
