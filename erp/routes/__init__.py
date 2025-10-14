import importlib, pkgutil, sys
from flask import Blueprint

# Known blueprints you may have; add to this list if needed
KNOWN = [
    "erp.routes.main",
    "erp.routes.auth",
    "erp.routes.inventory",
    "erp.routes.finance",
    "erp.routes.procurement",
    "erp.routes.sales",
    "erp.routes.crm",
    "erp.routes.hr",
]

def register_blueprints(app):
    seen = set()
    for modpath in KNOWN:
        try:
            m = importlib.import_module(modpath)
        except Exception as e:
            app.logger.warning(f"[bp] Skipped {modpath}: {e}")
            continue
        for name in dir(m):
            obj = getattr(m, name)
            if isinstance(obj, Blueprint) and obj.name not in seen:
                app.register_blueprint(obj)
                seen.add(obj.name)
                app.logger.info(f"[bp] Registered {obj.name} from {modpath}")
