# Minimal WSGI shim to expose `app` from the app factory
from erp import create_app  # assumes erp/__init__.py defines create_app()
app = create_app()
