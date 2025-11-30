# tools/scan_blueprints.py
"""
Utility to scan the `erp` package and register all Flask blueprints
that follow common naming conventions.

This is intended as a helper / debugging tool and is not required
for normal app startup. It can be used from a shell like:

    from erp.app import create_app
    from tools.scan_blueprints import register_all

    app = create_app()
    count = register_all(app)
    print(f"Registered {count} blueprints")

"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable, List

from flask import Blueprint


def _iter_erp_modules() -> Iterable[str]:
    """Yield full module names under the `erp` package."""
    import erp  # local import so this file can be imported without erp installed in sys.path

    for _finder, name, _ispkg in pkgutil.walk_packages(erp.__path__, prefix="erp."):
        yield name


def _find_blueprints(module) -> List[Blueprint]:
    """Return all Blueprint-like attributes in a module."""
    candidates: List[Blueprint] = []
    for attr_name in ("bp", "blueprint", "Blueprint", "api", "router"):
        if hasattr(module, attr_name):
            obj = getattr(module, attr_name)
            if isinstance(obj, Blueprint):
                candidates.append(obj)
    return candidates


def register_all(app) -> int:
    """Scan all `erp.*` modules and register any found Blueprints on `app`.

    Returns the number of blueprints successfully registered.
    """
    count = 0

    for modname in _iter_erp_modules():
        try:
            module = importlib.import_module(modname)
        except Exception:
            # If an import explodes, we just skip that module.
            # In the future, we could log this instead of silent skip.
            continue

        for bp in _find_blueprints(module):
            try:
                app.register_blueprint(bp)
                count += 1
            except Exception:
                # Blueprint registration failed; ignore for this helper.
                # Better would be to log details.
                continue

    return count
