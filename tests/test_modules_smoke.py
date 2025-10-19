import importlib
import pkgutil

import erp.routes
from erp import create_app


def test_blueprints_registered():
    app = create_app()
    # iterate over all modules in erp.routes package
    module_iter = pkgutil.iter_modules(erp.routes.__path__)
    with app.app_context():
        for mod in module_iter:
            module = importlib.import_module(f"erp.routes.{mod.name}")
            bp = getattr(module, "bp", None)
            assert bp is not None, f"{mod.name} missing bp"
            assert bp.name in app.blueprints, f"{bp.name} not registered"


