# erp/tools/freeze_blueprints.py
from __future__ import annotations
import importlib, pkgutil, sys, os, json
from pathlib import Path
from typing import List, Tuple

from erp import create_app

# Packages to scan for Blueprint instances
SCAN_PACKAGES = [
    "erp.api",
    "erp.views",
    "erp.modules",
    "erp.features",
]

def discover_blueprints() -> List[Tuple[str, str]]:
    """Return list of ('importable.module:bpvar', '/url_prefix')."""
    found: List[Tuple[str, str]] = []

    for pkg in SCAN_PACKAGES:
        try:
            m = importlib.import_module(pkg)
        except Exception:
            continue
        if not hasattr(m, "__path__"):
            continue
        for modinfo in pkgutil.walk_packages(m.__path__, m.__name__ + "."):
            name = modinfo.name
            try:
                mod = importlib.import_module(name)
            except Exception:
                continue
            for attr in dir(mod):
                obj = getattr(mod, attr, None)
                # Basic fingerprint of a Blueprint
                if obj.__class__.__name__ == "Blueprint" and getattr(obj, "name", None):
                    # default prefix is '/' + blueprint.name unless module defines URL_PREFIX
                    prefix = getattr(mod, "URL_PREFIX", f"/{obj.name}")
                    found.append((f"{name}:{attr}", prefix))
    return found

def main(out_path: str | None = None) -> None:
    # Ensure the app imports (use sqlite fallback via env or app config)
    app = create_app({"SQLALCHEMY_DATABASE_URI": os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite://")})
    with app.app_context():
        pairs = discover_blueprints()
        pairs.sort(key=lambda x: x[0].lower())

    out = Path(out_path) if out_path else Path(__file__).resolve().parent.parent / "blueprints_explicit.py"
    lines = [
        "# AUTO-GENERATED. Do not hand-edit.",
        "from importlib import import_module",
        "",
        "def _load(spec):",
        "    mod, var = spec.split(':', 1)",
        "    return getattr(import_module(mod), var)",
        "",
        "EXPLICIT_BLUEPRINTS = [",
    ]
    for spec, prefix in pairs:
        lines.append(f"    (_load('{spec}'), {prefix!r}),")
    lines.append("]\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
