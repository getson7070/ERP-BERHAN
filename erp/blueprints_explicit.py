# AUTO-GENERATED. Do not hand-edit.
from importlib import import_module

def _load(spec):
    mod, var = spec.split(':', 1)
    return getattr(import_module(mod), var)

EXPLICIT_BLUEPRINTS = [
    (_load('erp.api.integrations:integrations_bp'), '/integrations'),
    (_load('erp.views.main:bp'), '/main'),
]
