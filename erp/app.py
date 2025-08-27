"""Application utilities for BERHAN ERP."""

import importlib
import pkgutil


def _scan(package: str, app) -> None:
    """Recursively import modules under *package* and register ``bp`` blueprints."""
    try:
        pkg = importlib.import_module(package)
    except ModuleNotFoundError:
        return

    bp = getattr(pkg, "bp", None)
    if bp is not None and bp.name not in app.blueprints:
        app.register_blueprint(bp)

    for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        if ispkg:
            _scan(modname, app)
        else:
            try:
                mod = importlib.import_module(modname)
            except Exception:
                continue
            bp = getattr(mod, "bp", None)
            if bp is not None and bp.name not in app.blueprints:
                app.register_blueprint(bp)


def register_blueprints(app) -> None:
    """Auto-discover and register blueprints.

    Scans the ``erp.routes``, ``erp.blueprints`` and ``plugins`` packages for
    modules exposing a module-level ``bp`` blueprint. See ``docs/blueprints.md``
    for additional background on this convention.
    """
    for package in ("erp.routes", "erp.blueprints", "plugins"):
        _scan(package, app)
