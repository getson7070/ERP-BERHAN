import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app


def test_core_module_blueprints_registered():
    app = create_app()
    modules = ["crm", "hr", "procurement", "manufacturing", "projects"]
    for mod in modules:
        assert mod in app.blueprints


